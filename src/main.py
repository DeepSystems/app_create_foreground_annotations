import os
import supervisely_lib as sly
import constants
import utils


def main():
    sly.logger.info("APPLICATION_STARTED")

    task_id = int(os.getenv("TASK_ID"))
    api = sly.Api.from_env()
    api.add_additional_field('taskId', task_id)
    api.add_header('x-task-id', str(task_id))

    task_context = api.task.get_context(task_id)
    team_id = task_context["team"]["id"]
    workspace_id = task_context["workspace"]["id"]

    gui_template = ""
    with open('gui.html', 'r') as file:
        gui_template = file.read()

    data = {}
    data["projects"] = utils.read_projects(api, workspace_id)

    payload = {}
    payload["template"] = gui_template
    payload["state"] = constants.DEFAULTS
    payload["data"] = data

    #"http://192.168.1.42/apps/2/sessions/54"
    jresp = api.task.set_data(task_id, payload)

    pass

if __name__ == "__main__":
    main()


#54