

def get_failed_update_from_results(results):
    return [str(x["name"]).lower() for x in results
            if x.get("updated", None) is not None and x.get("name", None) is not None and not x["updated"]]


def get_staged_projects_without_failed_update(staged_projects, failed_update):
    return [p for p in staged_projects
            if p.get("name", None) is not None and str(p["name"]).lower() not in failed_update]
