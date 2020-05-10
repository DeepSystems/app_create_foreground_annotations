import argparse
import json
import os
import time
import cv2
import numpy as np
import skimage
import random
import supervisely_lib as sly
import constants as const
from supervisely_lib.annotation.json_geometries_map import GET_GEOMETRY_FROM_STR
import math

#@TODO: for debug
random.seed(7)


DEBUG = True

#@TODO: учитывать дырки в объекте
#@TODO: выкидывать там, где много серой зоны по площади ли по количеству
#@TODO: по компонентам связности крестик, без диагональных пикселей

def update_progress(api, task_id, percentage):
    api.task.set_data(task_id, payload=int(percentage), field="{}.{}".format(const.DATA, const.PROGRESS))


def count_instances_area(mask, cc_count):
    _total_sum = 0
    cc_area = []
    for i in range(cc_count + 1):  # skip zero mask - background
        area = np.count_nonzero(mask == i)
        _total_sum += area
        if i == 0:
            continue
        cc_area.append((i, area))
    image_pixels_count = mask.shape[0] * mask.shape[1]
    if _total_sum != image_pixels_count:
        raise AssertionError("Some pixels are missed. Processed {} of {}".format(_total_sum, image_pixels_count))
    cc_area = sorted(cc_area, key=lambda tup: tup[1], reverse=True)
    return cc_area


# clean project annotations + set new meta
def set_project_meta(api, project_id, state):
    fg_class = sly.ObjClass(state[const.FG_NAME],
                            GET_GEOMETRY_FROM_STR(state[const.FG_SHAPE]),
                            color=sly.color.hex2rgb(state[const.FG_COLOR]))
    st_class = sly.ObjClass(state[const.ST_NAME],
                            GET_GEOMETRY_FROM_STR(state[const.ST_SHAPE]),
                            color=sly.color.hex2rgb(state[const.ST_COLOR]))
    meta = sly.ProjectMeta(obj_classes=sly.ObjClassCollection([fg_class, st_class]))
    api.project.update_meta(project_id, sly.ProjectMeta().to_json())  # clear previous labels and classes
    api.project.update_meta(project_id, meta.to_json())
    return fg_class, st_class


def reset_buttons_and_progress(api, task_id):
    update_progress(api, task_id, 0)
    api.task.set_data(task_id, payload={const.RUN_CLICKED: False, const.STOP_CLICKED: False}, field=const.STATE, append=True)


def extract_foreground():
    api = sly.Api.from_env()
    task_id = int(os.getenv("TASK_ID"))

    try:
        if DEBUG:
            sly.fs.mkdir(const.DEBUG_VIS_DIR)
            sly.fs.clean_dir(const.DEBUG_VIS_DIR)

        state = api.task.get_data(task_id, field=const.STATE)

        project = api.task.get_data(task_id, field="{}.projects[{}]".format(const.DATA, state[const.PROJECT_INDEX]))
        project_id = project["id"]

        workspace_id = api.project.get_info_by_id(project_id).workspace_id
        team_id = api.workspace.get_info_by_id(workspace_id).team_id

        processed_items = []
        api.task.set_data(task_id, payload=processed_items, field="{}.{}".format(const.DATA, const.TABLE))

        # sample images
        all_images = []
        for dataset in api.dataset.get_list(project_id):
            images = api.image.get_list(dataset.id)
            image_dataset = [dataset] * len(images)
            all_images.extend(zip(images, image_dataset))

        # read sample count
        if state[const.SAMPLE_FLAG]:
            cnt_images = state[const.SAMPLE_COUNT]
            assert cnt_images <= len(all_images)
            random.shuffle(all_images)
            all_images = all_images[:cnt_images]

        fg_class, st_class = set_project_meta(api, project_id, state)

        sly.fs.mkdir(const.CACHE_DIR)
        for idx, (image_info, dataset_info) in enumerate(all_images):
            table_row = {}
            image_id = image_info.id
            table_row['id'] = image_id
            sly.logger.debug("---> image_id = {}".format(image_id))

            if DEBUG:
                debug_img_dir = os.path.join(const.DEBUG_VIS_DIR, str(image_id))
                sly.fs.mkdir(debug_img_dir)

            image_url = api.image.url(team_id, workspace_id, project_id, dataset_info.id, image_id)
            table_row['name'] = '<a href="{0}" rel="noopener noreferrer" target="_blank">{1}</a>' \
                                .format(image_url, image_info.name)

            image_path = os.path.join(const.CACHE_DIR, "{}.png".format(image_id))
            if not sly.fs.file_exists(image_path):
                api.image.download_path(image_id, image_path, )
            image = sly.image.read(image_path, remove_alpha_channel=False)

            if image.shape[2] != 4:
                sly.logger.warning("Image (id = {}) is skipped: it does not have alpha channel".format(image_id))
                continue
            if DEBUG:
                sly.image.write(os.path.join(debug_img_dir, '000_image.png'), image, remove_alpha_channel=False)

            alpha = image[:, :, 3]
            if DEBUG:
                sly.image.write(os.path.join(debug_img_dir, '001_alpha.png'), alpha)

            # extract foreground pixels
            mask = (alpha >= state[const.ALPHA_THRESHOLD]).astype(np.uint8) * 255
            if DEBUG:
                sly.image.write(os.path.join(debug_img_dir, '002_mask.png'), mask)

            # create mask for all connected components
            mask_instances, num_cc = skimage.measure.label(mask, background=0, return_num=True)
            if DEBUG:
                vis = skimage.color.label2rgb(mask_instances, bg_label=0)
                sly.image.write(os.path.join(debug_img_dir, '003_mask_cc.png'), vis * 255)
            table_row['total objects'] = num_cc

            # remove small objects
            area_pixels = int(mask_instances.shape[0] * mask_instances.shape[1] / 100 * state[const.AREA_THRESHOLD])
            mask_cleaned = skimage.morphology.remove_small_objects(mask_instances, area_pixels)
            mask_cleaned, num_cc = skimage.measure.label(mask_cleaned, background=0, return_num=True)
            if DEBUG:
                vis = skimage.color.label2rgb(mask_cleaned, bg_label=0)
                sly.image.write(os.path.join(debug_img_dir, '004_mask_cleaned.png'), vis * 255)

            cc_area = count_instances_area(mask_cleaned, num_cc)
            cc_area = cc_area[:state[const.MAX_NUMBER_OF_OBJECTS]]

            table_row['final objects'] = len(cc_area)

            labels = []
            sly.logger.debug("image_id = {}, number of extracted objects: {}".format(image_id, len(cc_area)))
            for cc_color, area in cc_area:
                object_mask = (mask_cleaned == cc_color)
                geometry = sly.Bitmap(data=object_mask)
                label = sly.Label(geometry, fg_class)
                labels.append(label)

            #find gray zone
            gray_zone = np.logical_and(alpha != 0, alpha != 255)
            if np.sum(gray_zone) != 0:
                #gray_zone is not empty
                gray_geometry = sly.Bitmap(data=gray_zone)
                gray_label = sly.Label(gray_geometry, st_class)
                labels.append(gray_label)

            table_row['gray area (%)'] = round(np.sum(gray_zone) * 100 / (gray_zone.shape[0] * gray_zone.shape[1]), 2)

            ann = sly.Annotation(mask.shape[:2], labels=labels)

            if DEBUG:
                render = np.zeros(ann.img_size + (3,), dtype=np.uint8)
                ann.draw(render)
                sly.image.write(os.path.join(debug_img_dir, '005_ann.png'), render)

            api.annotation.upload_ann(image_id, ann)
            processed_items.append(table_row)

            #time.sleep(2)
            if (idx % const.NOTIFY_EVERY == 0 and idx != 0) or idx == len(all_images) - 1:
                api.task.set_data(task_id, payload=processed_items, field="{}.{}".format(const.DATA, const.TABLE), append=True)
                processed_items = []
                update_progress(api, task_id, (idx + 1) * 100 / len(all_images))
                need_stop = api.task.get_data(task_id, field="{}.{}".format(const.STATE, const.STOP_CLICKED))
                if need_stop is True:
                    reset_buttons_and_progress(api, task_id)
                    sly.logger.info("SCRIPT IS STOPPED")
                    exit(0)
    except Exception as e:
        sly.logger.critical('Unexpected exception', exc_info=True, extra={
            'event_type': sly.EventType.TASK_CRASHED,
            'exc_str': str(e),
        })
        sly.logger.debug('Script finished: ERROR')
    else:
        sly.logger.debug('Script finished: OK')
    finally:
        reset_buttons_and_progress(api, task_id)
        pass


if __name__ == "__main__":
    extract_foreground()
