
def read_projects(api, workspace_id):
    res = []
    #_ids = [ ]
    projects = api.project.get_list(workspace_id)
    for idx, project in enumerate(projects):
        item = {}
        item["id"] = project.id
        #_ids.append(project.id)
        item["name"] = project.name
        item["imagesCount"] = api.project.get_images_count(project.id)
        item["index"] = idx
        res.append(item)
    return res