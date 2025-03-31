import { defineStore } from "pinia"

export const useSystemStore = defineStore('system', {
    state: () => ({
        settings: {},
        listingInProgress: false,
        migrationInProgress: false,
        stagedProjects: new Set(),
        stagedGroups: new Set(),
        stagedUsers: new Set(),
        directTransferGeneratedRequest: new Object(),
        directTransferModifiedRequest: new Object()
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
        async updateDirectTransferGeneratedRequest(request) {
            this.directTransferGeneratedRequest = request
        },
        async updateDirectTransferModifiedRequest(request) {
            this.directTransferModifiedRequest = request
        },
        async stageProject(pid) {
            await this.stagedProjects.add(pid)
        },
        async unstageProject(pid) {
            await this.stagedProjects.delete(pid)
        },
        async stageGroup(gid) {
            await this.stagedGroups.add(gid)
        },
        async unstageGroup(gid) {
            await this.stagedGroups.delete(gid)
        },
        async stageUser(uid) {
            await this.stagedUsers.add(uid)
        },
        async unstageUser(uid) {
            await this.stagedUsers.delete(uid)
        }
    }
})
