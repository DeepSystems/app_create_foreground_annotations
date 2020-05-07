import json
import supervisely_lib as sly
from supervisely_lib.io.json import load_json_file, dump_json_file



state = None
if sly.fs.file_exists(sly.TaskPaths.TASK_CONFIG_PATH):
    app_config = load_json_file(sly.TaskPaths.TASK_CONFIG_PATH)
    state = app_config[STATE]
else:



def main():
    pass


if __name__ == "__main__":
    sly.main_wrapper('CALC_STATS', main)

