# 根因分析（Day 8 独立检验）

> 每个缺陷写四行：现象 / 根因 / 修复 / 如何防复发。
> 最后一段写：你新增的测试为什么能暴露“隐藏缺陷”。

## 缺陷 1：现象、根因、修复、如何防复发

- 现象：工具执行了 3 次，会多执行一次
- 根因：判断失败的时候用了 >2 才报错，那么这样 fail count = 0,1,2 已经执行了3 次都不会报错，
- 修复：改成 >=2 的时候就报错，这样就会只执行 2 次
- 如何防复发：将阈值提成具名产量

## 缺陷 2：现象、根因、修复、如何防复发

- 现象：工具最多执行 2 次就报错退出了
- 根因：当成功执行的时候没有清0
- 修复：在第133 行 ` fail_counts[name] = 0` 没有报错的时候就清 0
- 如何防复发：

## 缺陷 3（隐藏缺陷）：现象、根因、修复、如何防复发

- 现象：在app.py 的 ToolRegistry中，不同对象注册的工具会互相影响
- 根因：在app.py 的第 65 行中 ，给对象属_tools赋值的时候，使用了可变的默认参数 {},它在函数定义时只求值一次。也就是说，整个程序运行期间，这个空字典只有一个，被所有没传 tools 的实例共用
- 修复：在赋值的时候赋值的时候 重新拷贝一份 ` self._tools = dict(tools) if tools is not None else {}`

- 如何防复发：从签名上消灭可变默认值类型 ，函数签名改成
`tools: dict[str, Callable[[dict[str, Any]], str]] | None = None`

## 我新增的测试

- 新增了哪些用例：
```python
class SameToolRegistryObj(unittest.TestCase):
    def test_tool_registry(self)->None:
        registry_a = app.ToolRegistry()
        registry_b = app.ToolRegistry()
        registry_a.register("get_today", app.get_today)
        registry_b.register("get_weather",app.get_weather)
        
        #这时候a 中不应该有 get_weather ,b 不应该污染 a
        self.assertNotIn("get_weather",registry_a.names())
        self.assertNotIn("get_today",registry_b.names())

```
- 为什么它们能暴露问题（而不是只测实现细节）：
