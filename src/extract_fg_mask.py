import argparse
import json
import os
import cv2
import numpy as np
import skimage
import supervisely_lib as sly

parser = argparse.ArgumentParser(description='Recalculate foreground label')
parser.add_argument('--image-id', action="store", type=int, required=True)
parser.add_argument('--state', action="store", type=json.loads, default={}, required=True)

parser.add_argument('--fg-alpha-threshold', action="store", type=sly.color.check_channel_value, default=250,
                    help="0 means fully transparent, 255  - no transparency."
                         "keep all pixels with transparency great or equal (>=)")

parser.add_argument('--cache-dir', action="store", type=str, default="/sly_task_data/cache", required=False)
parser.add_argument('--vis-dir', action="store", type=str, default="/sly_task_data/vis", required=False)
parser.add_argument('--debug-vis', action="store_true", default=False, required=False)

# example
# --image-id 339 --state "{\"key\":\"val\"}" --debug-vis
#363

def demo_test():
    args = parser.parse_args()

    import matplotlib.pyplot as plt
    import matplotlib.patches as mpatches

    from skimage import data
    from skimage.filters import threshold_otsu
    from skimage.segmentation import clear_border
    from skimage.measure import label, regionprops
    from skimage.morphology import closing, square
    from skimage.color import label2rgb

    image = data.coins()[50:-50, 50:-50]
    sly.image.write(os.path.join(args.vis_dir, 'image.png'), image)

    # apply threshold
    thresh = threshold_otsu(image)
    bw = closing(image > thresh, square(3))

    # remove artifacts connected to image border
    cleared = clear_border(bw)

    # label image regions
    label_image = label(cleared)
    # to make the background transparent, pass the value of `bg_label`,
    # and leave `bg_color` as `None` and `kind` as `overlay`
    image_label_overlay = label2rgb(label_image, image=image, bg_label=0)

    fig, ax = plt.subplots(figsize=(10, 6))
    ax.imshow(image_label_overlay)

    for region in regionprops(label_image):
        # take regions with large enough areas
        if region.area >= 100:
            # draw rectangle around segmented coins
            minr, minc, maxr, maxc = region.bbox
            rect = mpatches.Rectangle((minc, minr), maxc - minc, maxr - minr,
                                      fill=False, edgecolor='red', linewidth=2)
            ax.add_patch(rect)

    ax.set_axis_off()
    plt.tight_layout()
    plt.show()

def extract_foreground():
    args = parser.parse_args()
    sly.logger.info("arguments", extra={"cmd_args": vars(args)})

    sly.fs.mkdir(args.cache_dir)
    sly.fs.mkdir(args.vis_dir)
    sly.fs.clean_dir(args.vis_dir)

    #demo_test()
    #return

    api = sly.Api.from_env()

    image_path = os.path.join(args.cache_dir, "{}.png".format(args.image_id))
    image = None
    if not sly.fs.file_exists(image_path):
        api.image.download_path(args.image_id, image_path)
    image = sly.image.read(image_path, remove_alpha_channel=False)
    if image.shape[2] != 4:
        sly.logger.critical("Image (id = {}) does not have alpha channel".format(args.image_id))

    alpha = image[:, :, 3]
    mask = (alpha >= args.fg_alpha_threshold).astype(np.uint8) * 255

    if args.debug_vis:
        cv2.imwrite(os.path.join(args.vis_dir, 'alpha.png'), mask)

    labeled_image, num = skimage.measure.label(mask, background=0, return_num=True)
    print(num)

    # "https://scikit-image.org/docs/dev/auto_examples/segmentation/plot_label.html"
    colored_labels = skimage.color.label2rgb(labeled_image, bg_label=0)
    if args.debug_vis:
        sly.image.write(os.path.join(args.vis_dir, 'components.png'), colored_labels * 255)


    # img_colorized = cv2.applyColorMap(labeled_image.astype(np.uint8), cv2.COLORMAP_RAINBOW)
    # if args.debug_vis:
    #     cv2.imwrite(os.path.join(args.vis_dir, 'components.png'), img_colorized)

    # total_sum = 0
    # for i in range(num + 1):
    #     comp_mask = (labeled_image == i).astype(np.uint8)
    #     cv2.imwrite(os.path.join(args.vis_dir, "comp_{}.png".format(i)),  comp_mask * 255)
    #     total_sum += comp_mask.sum()
    #     print(comp_mask.sum())
    #
    # sly.logger.info("SCRIPT EXECUTED")
    # print('total_sum = ', total_sum, '; total pixels = ', alpha.shape[0] * alpha.shape[1])




if __name__ == "__main__":
    sly.main_wrapper('EXTRACT_FG_MASK', extract_foreground)
