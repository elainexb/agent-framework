"""Local read-only Agent catalog; execution and evaluation belong to later tickets."""
from __future__ import annotations

import argparse
import os

from .catalog import agent_catalog
from .config import PROJECT_ROOT


def catalog_view(selected: str | None) -> dict:
    reports = agent_catalog()
    names = [report["name"] for report in reports]
    if selected is None and names:
        selected = names[0]
    report = next((item for item in reports if item["name"] == selected), None)
    return {"choices": names, "selected": selected if report else None, "report": report}


def build_page():
    os.environ["GRADIO_ANALYTICS_ENABLED"] = "False"
    os.environ["HF_HUB_OFFLINE"] = "1"
    import gradio as gr

    def reload(selected):
        view = catalog_view(selected)
        report = view["report"]
        selector_update = gr.Dropdown(choices=view["choices"], value=view["selected"])
        if report is None:
            return selector_update, "没有可显示的 Agent，请通过 Codex 搭建或重新选择。", "", "", [], None
        rows = []
        for key, label in (("configuration", "配置检查"), ("tools", "工具源码检查"),
                           ("build", "搭建/业务验收"), ("model", "模型验证"), ("runtime", "网页试跑")):
            rows.append([label, report[key]["status"], report[key]["detail"]])
        return (selector_update, report["description"],
                f'{report["model"]["provider"] or "未知"} / {report["model"]["name"] or "未知"}',
                report["source_version"] or "配置检查失败，未生成版本",
                rows, report)

    with gr.Blocks(title="Agent 配置工作台", analytics_enabled=False) as page:
        gr.Markdown("# Agent 配置工作台\n通过 Codex 新建或修改 Agent，在这里核对同一份配置。")
        gr.Markdown("**当前仅提供配置入口。** 模型未验证，网页试跑尚未接通。配置检查通过不代表 Agent 已可运行。")
        with gr.Row():
            selector = gr.Dropdown(label="选择 Agent", choices=[], interactive=True)
            refresh = gr.Button("重新载入列表与配置")
        description = gr.Textbox(label="Agent 用途", interactive=False)
        model = gr.Textbox(label="声明的模型（权重版本未验证）", interactive=False)
        version = gr.Textbox(label="配置与代码版本（不含模型权重、数据或环境）", interactive=False)
        checks = gr.Dataframe(headers=["检查项", "状态", "说明"], datatype=["str", "str", "str"],
                              value=[], interactive=False, label="检查结果")
        gr.Markdown("PASS：该项检查通过；FAIL：该项阻断；UNKNOWN：缺少验证证据。\n\n"
                    "版本包含 agent.yaml、instructions.md、tools.py、services.py 和公共基础指令。"
                    "修改配置后点击重新载入；工具源码检查不会导入或执行工具。")
        with gr.Accordion("同源检查报告（与命令行 inspect 相同）", open=False):
            report = gr.JSON(label="检查报告")
        outputs = [selector, description, model, version, checks, report]
        refresh.click(reload, inputs=selector, outputs=outputs, queue=False, api_name=False)
        selector.input(reload, inputs=selector, outputs=outputs, queue=False, api_name=False)
        page.load(reload, inputs=selector, outputs=outputs, queue=False, api_name=False)
    return page


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Local read-only Agent configuration workbench")
    parser.add_argument("--port", type=int, default=7863)
    args = parser.parse_args(argv)
    if not 1 <= args.port <= 65535:
        parser.error("--port must be between 1 and 65535")
    bypass = set(filter(None, (os.environ.get("NO_PROXY", "") + "," + os.environ.get("no_proxy", "")).split(",")))
    bypass.update({"127.0.0.1", "localhost"})
    os.environ["NO_PROXY"] = os.environ["no_proxy"] = ",".join(sorted(bypass))
    page = build_page()
    page.launch(server_name="127.0.0.1", server_port=args.port, share=False, inbrowser=False,
                enable_monitoring=False, allowed_paths=[], blocked_paths=[str(PROJECT_ROOT)],
                footer_links=[], ssr_mode=False)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
