import supervisely_lib as sly

CACHE_DIR = "/sly_task_data/cache"
STATE_PATH = sly.TaskPaths.APP_STATE_PATH


# STATE
# state field names have to be in Camel case

FG_NAME = "fgName"
FG_SHAPE = "fgShape"
FG_COLOR = "fgColor"

FG_SHAPE_ANY = sly.AnyGeometry.geometry_name()
FG_SHAPE_BITMAP = sly.Bitmap.geometry_name()

#state fields
STATE = "state"
PROJECT_INDEX = "projectIndex"

SAMPLE_FLAG = "sampleFlag"
SAMPLE_COUNT = "sampleCount"

ALPHA_THRESHOLD = "alphaThreshold"
AREA_THRESHOLD = "areaThreshold"
MAX_NUMBER_OF_OBJECTS = "maxNumObjects"

LOGS_OPENED = "logsOpened"
PROGRESS = "progress"
LOADING = "loading"


STATE_DEFAULTS = {
    PROJECT_INDEX: 0,
    SAMPLE_FLAG: False,
    SAMPLE_COUNT: 1,

    ALPHA_THRESHOLD: 100,
    AREA_THRESHOLD: 5,
    MAX_NUMBER_OF_OBJECTS: 1,

    FG_NAME: "fg",
    FG_SHAPE: FG_SHAPE_ANY,
    FG_COLOR: sly.color.rgb2hex([0, 255, 0]),

    PROGRESS: 55,

    LOADING: False,

    LOGS_OPENED: [] #["logs"]
}

