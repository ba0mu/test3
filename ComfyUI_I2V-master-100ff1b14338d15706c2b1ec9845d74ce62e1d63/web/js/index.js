import { app } from "/scripts/app.js";
import { $el } from "/scripts/ui.js";

app.registerExtension({
    name: "Comfy.TemplateNode",

    async setup() {
        // 注入自定义样式文件
        // $el("link", {
        //     parent: document.head,
        //     rel: "stylesheet",
        //     type: 'text/css',
        //     href: "./extensions/ComfyUI-Template-Node/css/index.css",
        // });
        // 自定义JS逻辑
        console.log('init template node')
    },
});