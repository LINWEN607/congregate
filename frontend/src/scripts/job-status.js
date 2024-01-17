// Helper script to check for the existence of specific Celery tasks in API responses

export const listJobs = [
    'congregate.cli.list_source.list_data',
    'traverse-groups',
    'retrieve-projects',
    'retrieve-user'
]

export const migrateJobs = [
    'watch-import-status',
    'watch-import-entity-status',
    'post-migration-task'
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