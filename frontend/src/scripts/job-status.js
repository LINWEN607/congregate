// Helper script to check for the existence of specific Celery tasks in API responses

export const listJobs = [
    'list_data',
    'retrieve-bbs-users',
    'retrieve-bbs-projects',
    'retrieve-bbs-repos',
    'retrieve-bbs-user-groups',
    'retrieve-gh-users',
    'retrieve-gh-orgs',
    'retrieve-gh-repos',
    'retrieve-gl-users',
    'retrieve-gl-groups',
    'retrieve-gl-projects',
    'retrieve-ado-users',
    'retrieve-ado-projects',
    'retrieve-ado-groups'
]

export const migrateJobs = [
    'watch-import-status',
    'watch-import-entity-status',
    'post-migration-task',
    'trigger-bulk-import-task'
]

// This function is used to see if any of the values in a list are present
// in another array. It's similar in functionality to Python's any() function
export function matchFunction(list, data) {
    let match = null
    if (list.some(item => {
        if(data.hasOwnProperty(item)) {
            match = item
            return true
        }
    })) {
        return match
    }    
}