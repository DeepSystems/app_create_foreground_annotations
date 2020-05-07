# import time
# import os
# import pickle
#
# import supervisely_lib as sly
# import constants as const
# import utils
#
# #https://plotly.com/python/imshow/
#
#
# def main():
#     print("main")
#
#     sly.logger.info("!!! SERVER_ADDRESS", extra={'se': os.getenv("SERVER_ADDRESS")})
#     sly.logger.info("!!! API_TOKEN", extra={'se': os.getenv("API_TOKEN")})
#
#     task_id = int(os.getenv("TASK_ID"))
#     api = sly.Api.from_env()
#     api.add_additional_field('taskId', task_id)
#     api.add_header('x-task-id', str(task_id))
#
#     widgets = []
#
#     winput = sly.app_widget.Input.create(name="Image ID", description="Put image_id here", id=const.INPUT_IMAGE_ID, default_value="192")
#     widgets.append(winput)
#
#     wbutton = sly.app_widget.Button.create(name="Flip image",
#                                            description="Image will be flipped",
#                                            id=const.BUTTON_FLIP,
#                                            command="python /sly_task_data/app/src/draw.py")
#     widgets.append(wbutton)
#
#     wgallery = sly.app_widget.Gallery.create(name="g1", description="image and its flipped version", id=const.GALLERY_01)
#     widgets.append(wgallery)
#
#
#     sly.logger.info("!!! task_id ", extra={"app_id": task_id})
#
#     task_context = api.task.get_context(task_id)
#     team_id = task_context['team']['id']
#
#     report_id = api.report.create(team_id, "Demo app", widgets, layout="1fr / 1fr 1fr 1fr")
#     print(api.report.url(report_id))
#     sly.logger.info('Report URL', extra={'report_url': api.report.url(report_id)})
#
#     # save application id for all other scripts
#     utils.save(const.FILE_APP_ID, report_id)
#
#     #direct urls
#     #or base64 mix
#
#     while True:
#         time.sleep(5)
#
#

import supervisely_lib as sly


def main():
    sly.logger.info("APPLICATION_STARTED")

    



if __name__ == "__main__":
    main()


#54