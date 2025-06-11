---
title: "测试文档"
---
# Markdown 测试文档

> 本文档用于测试 Markdown 转换时的格式兼容性，涵盖绝大多数 Markdown 语法。

***

## 1. 标题（Headers）

# H1 标题
## H2 标题
### H3 标题
#### H4 标题
##### H5 标题
###### H6 标题

***

## 2. 强调（Emphasis）

**这是加粗文本**  
_这是斜体文本_  
~~这是删除线~~  
**加粗 _斜体_ 的组合**

***

## 3. 列表（Lists）

### 无序列表
- 项目 A
  - 子项目 A.1
    - 子子项目 A.1.1
- 项目 B

### 有序列表
1. 第一项
2. 第二项
   1. 第二项的子项
   2. 第二项的子项

***

## 4. 链接与图片（Links and Images）

[这是一个链接](https://www.example.com)

![图片示例](https://www.bing.com/images/search?view=detailV2&ccid=yhtM2yF9&id=9F1CAA199E3576CBC3ED1C81E3165F6D11DBE710&thid=OIP.yhtM2yF9xwY-6CoJFf9zGQHaE1&mediaurl=https%3a%2f%2fth.bing.com%2fth%2fid%2fR.ca1b4cdb217dc7063ee82a0915ff7319%3frik%3dEOfbEW1fFuOBHA%26riu%3dhttp%253a%252f%252fimg95.699pic.com%252fphoto%252f40005%252f9973.jpg_wh860.jpg%26ehk%3dCWROhjNoe4g3P9t73cljxauVT0PIqik4dFMdd7V3JJ8%253d%26risl%3d%26pid%3dImgRaw%26r%3d0&exph=561&expw=860&q=%e4%b8%8b%e9%9b%a8&simid=608010213098522869&FORM=IRPRST&ck=11612D08C3B69502B94047060BCF1670&selectedIndex=0&itb=0 "图片标题")

![](https://i-blog.csdnimg.cn/img_convert/cde0b0b1d9533c12b4ab0a6aeaf9f77b.png)
***

## 5. 引用（Blockquote）

> 这是一个引用段落。  
> 可用于引用他人言论或文档内容。

***

## 6. 代码（Code）

### 行内代码
请使用 `npm install` 命令安装依赖。

### 代码块
#### JavaScript 示例

```javascript
function greet(name) {
  console.log("Hello, " + name + "!");
}
greet("Markdown");
```

#### Python 示例

```python
def greet(name):
    print(f"Hello, {name}!")

greet("Markdown")
```

***

## 7. 表格（Tables）

| 姓名 | 年龄 | 城市     |
|------|------|----------|
| 张三 | 28   | 北京     |
| 李四 | 32   | 上海     |
| 王五 | 25   | 广州     |

***

## 8. 分隔线（Horizontal Rule）

***
***
___

***

## 9. 任务列表（Task List）

- [x] 支持粗体
- [x] 支持列表
- [ ] 支持未完成任务
- [x] 支持代码块

***

## 10. HTML 内嵌（Raw HTML）

<p style="color:red;">这是嵌入的 HTML 段落，文字为红色。</p>

***

## 11. 数学公式（MathJax）

当 $a \ne 0$，二次方程 $ax^2 + bx + c = 0$ 有解：
$$
x = \frac{-b \pm \sqrt{b^2 - 4ac}}{2a}
$$

***

## 12. 表情（Emoji）

支持 Emoji 😄 🎉 🚀

***

## 13. 折叠内容（<details> 标签）

<details>
  <summary>点击展开内容</summary>
  这是隐藏内容，可以通过点击展开查看。
</details>

***

## 14. 锚点链接（Internal Links）

前往 [代码块部分](#6-代码code)

***

*文档结束*
