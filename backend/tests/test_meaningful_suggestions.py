import pytest

from app.schemas.custom_resume import CustomResumeItem, has_meaningful_change


@pytest.mark.parametrize(("source", "suggested"), [
    ("负责简历上传校验、文字解析和页面交互。", "负责简历上传校验、文字解析和页面交互。"),
    ("▪ 在线体验：www.zhitucv.online；开源仓库：github.com/tianyuq94-pixel/zhitu-resume。",
     "在线体验：www.zhitucv.online；开源仓库：github.com/tianyuq94-pixel/zhitu-resume。"),
    ("熟悉 Vue，TypeScript 和 FastAPI。", "熟悉 Vue、TypeScript、FastAPI"),
    ("负责简历上传校验、文字解析和页面交互。", "负责页面交互，并完成简历上传校验与文字解析。"),
    ("使用 Vue 和 TypeScript 开发响应式页面，使用 FastAPI 开发后端接口。",
     "使用 Vue 和 TypeScript 开发响应式页面，并通过 FastAPI 完成后端接口开发。"),
    ("软件工程师，熟悉前后端开发及数据库设计", "软件工程师，熟悉前后端开发与数据库设计"),
])
def test_cosmetic_changes_are_not_suggestions(source, suggested):
    assert not has_meaningful_change(source, suggested)


def test_substantial_redundancy_removal_is_a_suggestion():
    assert has_meaningful_change(
        "负责页面开发工作，在项目开发过程中主要负责页面的开发和页面功能的开发工作。",
        "负责页面与功能开发。",
    )


@pytest.mark.parametrize("decision", ["pending", "accepted", "rejected"])
def test_old_cosmetic_records_keep_original_without_confirmation(decision):
    item = CustomResumeItem(
        source_text="▪ 在线体验：www.zhitucv.online",
        suggested_text="在线体验：www.zhitucv.online",
        reason="展示项目链接", decision=decision, final_text="在线体验：www.zhitucv.online",
    )
    assert not item.has_suggestion
    assert item.decision == "rejected"
    assert item.final_text == item.source_text


def test_manual_edits_are_never_lost():
    item = CustomResumeItem(source_text="原来的简历内容", suggested_text="原来的简历内容",
        reason="保留原文", decision="custom", final_text="用户自己修改的内容")
    assert not item.has_suggestion
    assert item.final_text == "用户自己修改的内容"
    assert item.decision == "custom"
