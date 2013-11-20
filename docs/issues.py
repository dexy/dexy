import requests
import json

api = "https://api.github.com"

def get_request(path, params=None):
    if not params:
        params = {}

    r = requests.get("%s%s" % (api, path), params=params)
    return r.json()


def save_issues_to_json(repo_owner, repo_name, filename):
    args = { 'owner' : repo_owner, 'name' : repo_name }
    path = "/repos/%(owner)s/%(name)s/issues" % args
    
    issues = {}
    
    raw_json_data = get_request(path, {'state' : 'open' })
    issues.update(dict((issue['number'], issue) for issue in raw_json_data))
    
    raw_json_data = get_request(path, {'state' : 'closed' })
    issues.update(dict((issue['number'], issue) for issue in raw_json_data))
    
    with open(filename, "wb") as f:
        json.dump(issues, f)

save_issues_to_json("dexy", "dexy", "issues.json")
save_issues_to_json("dexy", "dexy-user-guide", "docs-issues.json")
