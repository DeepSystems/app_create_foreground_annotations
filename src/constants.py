import supervisely_lib as sly

CACHE_DIR = "/sly_task_data/cache"
DEBUG_VIS_DIR = "/sly_task_data/vis"
STATE_PATH = sly.TaskPaths.APP_STATE_PATH


# STATE
# state field names have to be in Camel case

FG_NAME = "fgName"
FG_SHAPE = "fgShape"
FG_COLOR = "fgColor"

ST_NAME = "stName"
ST_SHAPE = "stShape"
ST_COLOR = "stColor"

#state fields
DATA = "data"
STATE = "state"
PROJECT_INDEX = "projectIndex"

SAMPLE_FLAG = "sampleFlag"
SAMPLE_COUNT = "sampleCount"

ALPHA_THRESHOLD = "alphaThreshold"
AREA_THRESHOLD = "areaThreshold"
MAX_NUMBER_OF_OBJECTS = "maxNumObjects"

LOGS_OPENED = "logsOpened"
PROGRESS = "progress"

RUN_CLICKED = "runClicked"
STOP_CLICKED = "stopClicked"


TABLE = "table"
PER_PAGE = "perPage"
PAGE_SIZES = "pageSizes"

STATE_DEFAULTS = {
    PROJECT_INDEX: 0,
    SAMPLE_FLAG: False,
    SAMPLE_COUNT: 1,

    ALPHA_THRESHOLD: 100,
    AREA_THRESHOLD: 5,
    MAX_NUMBER_OF_OBJECTS: 1,

    FG_NAME: "fg",
    FG_SHAPE: sly.AnyGeometry.geometry_name(),
    FG_COLOR: sly.color.rgb2hex([0, 255, 0]),

    ST_NAME: "st",
    ST_SHAPE: sly.AnyGeometry.geometry_name(),
    ST_COLOR: sly.color.rgb2hex([128, 128, 128]),

    PER_PAGE: 10,
    PAGE_SIZES: [10, 15, 20, 50, 100, 250, 500],

    LOGS_OPENED: [], #["logs"]

    RUN_CLICKED: False,
    STOP_CLICKED: False
}


FG_SHAPES = "fgShapes"
DATA_DEFAULTS = {
    PROGRESS: 0,
    FG_SHAPES: [
        {"name": "Any Shape", "value": sly.AnyGeometry.geometry_name()},
        {"name": "Bitmap", "value": sly.Bitmap.geometry_name()},
    ]
}


NOTIFY_EVERY = 1