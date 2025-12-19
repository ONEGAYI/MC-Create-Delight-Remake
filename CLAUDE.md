**修复模组列表流程**
1. 先使用`.claude/skills/search-mods-info/scripts/compare_modlist.py`查看错误信息
2. 去`docs/mods-list.md`查看应有的表格格式
3. 构建改正的脚本
   - 判断错误是顺序错误、还是不存在在表中的错误，对于后者，保持留空只有编号即
    ```markdown
    num|  |  |  | 
    ```
   - 必须使用 SWAP 交换整行，连带着名字、标签、描述一起，不允许只改名字造成名字描述等对不上
   - 修复后必须严格遵循原有的表格格式
    ```markdown
    num| Name | env | tag | description
    ```
4. 最后再次使用compare脚本检查

## 注意事项
- `CLAUDE.md`, 模组列表的更新提交时只需说明更新了相关文档(文档名称)即可，不需要完整列出具体改动
- 为模组建档一定使用对应技能

## 可用工具
注意: 这些工具都位于`.claude\skills\search-mods-info\scripts`

1. `classify_statistics.py`
   - 分类统计脚本
   - 统计新分类体系中各分类的模组数量分布

2. `update_modlist_numbers.py`
   - 模组列表行号更新脚本
   - 自动为mods-list.md中`<mod-table>`标签内的表格更新行号

3. `compare_modlist.py`
   - 模组列表对比脚本
    ```bash
    options:
        -h, --help            show this help message and exit
        -n, --number NUMBER   显示N个模组名称（从起始位置开始）
        -c, --compare COMPARE
                                比较N个模组的一致性（从起始位置开始）
        -s, --start START     起始位置（从1开始，默认为1）
    ```

4. `fix_modlist.py`
   - 模组列表 处理工具
     - 从`modlist.md`提取表格为`modlist.json`
     - 将json写入`modlist.md`
     - 以及其他功能
    ```bash
    usage: fix_modlist.py [-h] [-e] [-w] [-i INPUT] [-o OUTPUT] [-j JSON_FILE]
                        [--swap SWAP] [--check-number-from CHECK_NUMBER_FROM]      
                        [--check-number-to CHECK_NUMBER_TO] [-v]

    模组列表处理工具

    options:
    -h, --help            show this help message and exit
    -e, --extract         提取<mod-table>表格数据并保存为JSON格式
    -w, --write           将JSON数据写入到markdown文件的表格中
    -i, --input INPUT     输入的markdown文件路径 (默认:
                            D:\games\MC\.minecraft\versions\Create-Delight-
                            Remake\docs\mods-list.md)
    -o, --output OUTPUT   输出文件路径 (根据模式决定是JSON还是MD)
    -j, --json-file JSON_FILE
                            JSON文件路径 (用于-w或检查模式，默认:
                            D:\games\MC\.minecraft\versions\Create-Delight-
                            Remake\docs\mods-list.json)
    --swap SWAP           交换指定编号的模组，格式："[1-30, 10-9]" (支持多对交换)
    --insert INSERT       在指定编号位置插入新模组
    --insert-content INSERT_CONTENT
                            插入内容，格式为"name; env; tags; description"，用分号分隔
    --check-number-from CHECK_NUMBER_FROM
                            检查编号范围的起始编号
    --check-number-to CHECK_NUMBER_TO
                            检查编号范围的结束编号
    -v, --version         show program's version number and exit

    使用示例:
    fix_modlist.py -e                           # 使用默认路径提取表格
    fix_modlist.py -e -i input.md -o out.json   # 指定输入输出文件
    fix_modlist.py -e -i custom.md              # 指定输入文件，使用默认输出
    fix_modlist.py -w                           # 使用默认路径将JSON写入MD
    fix_modlist.py -w -j in.json -o out.md      # 指定JSON输入和MD输出文件
    fix_modlist.py -w -j custom.json            # 指定JSON文件，使用默认MD输出
    fix_modlist.py --check-number-from 1 --check-number-to 50    # 检查1-50号编号
    fix_modlist.py --swap "[1-30]"              # 交换编号1和30的模组
    fix_modlist.py --swap "[1-30, 10-9]"        # 交换多对模组编号
    fix_modlist.py --swap "[1-30]" -w           # 交换并自动更新markdown
    fix_modlist.py --swap "[1-30]" -j custom.json -o output.json  # 使用自定义文件
    fix_modlist.py --insert 51                  # 在51号位置插入空模组
    fix_modlist.py --insert 52 -j mods.json     # 在52号位置插入空模组并指定JSON文件
    fix_modlist.py --insert 53 --insert-content "TestMod; 双端类; #测试; 测试模组"  # 插入带内容的模组

   ⚠️ 重要提示:
   - swap功能默认不会覆盖源JSON文件，每次swap都基于原始数据
   - 多次swap操作必须指定-j参数覆盖源文件: --swap "[1-30]" -j source.json -o source.json
   - 推荐一次性交换所有需要的模组: --swap "[1-30, 10-9, 5-15]"
   - 使用 --insert 参数时，必须指定 -j 参数来覆盖源JSON文件，否则不会修改源文件
   - --insert 会自动更新所有大于等于插入位置的模组编号
    ```