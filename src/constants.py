import supervisely_lib as sly

CACHE_DIR = "/sly_task_data/cache"
STATE_PATH = sly.TaskPaths.APP_STATE_PATH


# STATE
# state field names have to be in Camel case

FG_NAME = "fgName"
FG_SHAPE = "fgShape"
FG_COLOR = "fgColor"


STATE = "state"
PROJECT_ID = "project"
SAMPLE_FLAG = "sampleFlag"
SAMPLE_PERCENT = "samplePercent"
ALPHA_THRESHOLD = "alphaThreshold"
AREA_THRESHOLD = "areaThreshold"
MAX_NUMBER_OF_OBJECTS = "maxNumObjects"

DEFAULTS = {
    PROJECT_ID: None,

    ALPHA_THRESHOLD: 100,
    AREA_THRESHOLD: 5,
    MAX_NUMBER_OF_OBJECTS: 1,

    SAMPLE_FLAG: True,
    SAMPLE_PERCENT: 20,

    FG_NAME: "fg",
    FG_SHAPE: "any",
    FG_COLOR: sly.color.rgb2hex([0, 255, 0])
}

