import { defineStore } from "pinia"

export const useSystemStore = defineStore('system', {
    state: () => ({
        settings: {},
        listingInProgress: false,
        migrationInProgress: false,
        stagedProjects: new Set(),
        stagedGroups: new Set(),
        stagedUsers: new Set()
    }),
    actions: {
        updateSettings(settings) {
            this.settings = settings
        },
        updateListingInProgress(state) {
            this.listingInProgress = state
        },
        updateMigrationInProgress(state) {
            this.migrationInProgress = state
        },
        stageProject(pid) {
            this.stagedProjects.add(pid)
        },
        unstageProject(pid) {
            this.stagedProjects.delete(pid)
        },
        stageGroup(gid) {
            this.stagedGroups.add(gid)
        },
        unstageGroup(gid) {
            this.stagedGroups.delete(gid)
        },
        stageUser(uid) {
            this.stagedUsers.add(uid)
        },
        unstageUser(uid) {
            this.stagedUsers.delete(uid)
        }
    }
})
