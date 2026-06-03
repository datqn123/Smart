import { apiJson } from "@/lib/api/http"
import type {
  RuntimeCustomMenuFolder,
  RuntimeCustomPage,
} from "@/features/custom-builder/runtime/customMenuRuntime"

export type BuilderMenuTree = {
  treeEtag: string
  folders: RuntimeCustomMenuFolder[]
}

export type FolderDraftBody = {
  key: string
  label: string
  icon?: string
  description?: string
  visibilityRoles?: string[]
  sortOrder?: number
  etag?: string
}

export type PageDraftBody = {
  parentKey: string
  key: string
  label: string
  icon?: string
  description?: string
  routePath: string
  entityKey: string
  pageType: RuntimeCustomPage["pageType"]
  visibilityRoles?: string[]
  entityPermission?: string
  dataPermission?: string
  sortOrder?: number
  etag?: string
}

export function getCustomMenuTree() {
  return apiJson<BuilderMenuTree>("/api/v1/custom/menu-tree", {
    method: "GET",
    auth: true,
  })
}

export function createCustomMenuFolder(body: FolderDraftBody) {
  return apiJson<BuilderMenuTree>("/api/v1/custom/menu-folders", {
    method: "POST",
    auth: true,
    body: JSON.stringify(body),
  })
}

export function patchCustomMenuFolder(folderKey: string, body: FolderDraftBody) {
  return apiJson<BuilderMenuTree>(`/api/v1/custom/menu-folders/${encodeURIComponent(folderKey)}`, {
    method: "PATCH",
    auth: true,
    body: JSON.stringify(body),
  })
}

export function createCustomMenuPage(body: PageDraftBody) {
  return apiJson<BuilderMenuTree>("/api/v1/custom/menu-pages", {
    method: "POST",
    auth: true,
    body: JSON.stringify(body),
  })
}

export function patchCustomMenuPage(pageKey: string, body: PageDraftBody) {
  return apiJson<BuilderMenuTree>(`/api/v1/custom/menu-pages/${encodeURIComponent(pageKey)}`, {
    method: "PATCH",
    auth: true,
    body: JSON.stringify(body),
  })
}

export function publishCustomMenu(treeEtag?: string) {
  return apiJson<BuilderMenuTree>("/api/v1/custom/menu/publish", {
    method: "POST",
    auth: true,
    body: JSON.stringify({ scope: "all", etag: treeEtag }),
  })
}

export function getRuntimeCustomMenu() {
  return apiJson<BuilderMenuTree>("/api/v1/custom/runtime-menu", {
    method: "GET",
    auth: true,
  })
}

export function getRuntimeCustomPage(pageKey: string) {
  return apiJson<BuilderMenuTree>(`/api/v1/custom/pages/${encodeURIComponent(pageKey)}/runtime`, {
    method: "GET",
    auth: true,
  })
}
