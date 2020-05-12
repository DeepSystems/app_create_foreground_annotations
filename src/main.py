import os
import json
import html

import supervisely_lib as sly
import constants as const
import utils


def main():
    task_id = int(os.getenv("TASK_ID"))
    api = sly.Api.from_env()
    api.add_additional_field('taskId', task_id)
    api.add_header('x-task-id', str(task_id))

    task_context = api.task.get_context(task_id)
    team_id = task_context["team"]["id"]
    workspace_id = task_context["workspace"]["id"]

    gui_template = ""
    with open('/workdir/src/gui.html', 'r') as file:
        gui_template = file.read()

    #@TODO: filter non-image project
    #@TODO: replace to id
    projects = utils.read_projects(api, workspace_id)

    table = []
    for i in range(40):
        table.append({"name": sly.rand_str(5), "my_value": i})

    data = const.DATA_DEFAULTS
    data["projects"] = projects
    data["taskId"] = task_id
    data[const.TABLE] = table

    payload = {}
    payload["template"] = gui_template
    payload[const.STATE] = const.STATE_DEFAULTS
    #@TODO: for debug
    payload[const.STATE][const.PROJECT_INDEX] = len(data["projects"]) - 1
    payload[const.DATA] = data

    #http://192.168.1.42/apps/sessions/54
    #"http://192.168.1.42/apps/2/sessions/54"
    jresp = api.task.set_data(task_id, payload)

    sly.logger.info("APP_STARTED")

    pass

if __name__ == "__main__":
    main()


#54