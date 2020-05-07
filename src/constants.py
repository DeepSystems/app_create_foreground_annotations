import supervisely_lib as sly

CACHE_DIR = "/sly_task_data/cache"
STATE_PATH = sly.TaskPaths.APP_STATE_PATH


# STATE
# state field names have to be in Camel case

FG_NAME = "fg"
FG_COLOR = [0, 255, 0]
FG_SHAPE = "any"  # or "bitmap" or "any"

STATE = "state"
PROJECT_ID = "projectId"
DATASET_ID = "datasetId"

