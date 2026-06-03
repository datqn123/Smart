package com.example.smart_erp.custominterface.response;

import java.util.List;

public record CustomMenuTreeData(String treeEtag, List<CustomMenuFolderData> folders) {
}
