import os
import sys
import yaml
import subprocess


def check_each_plugin(plugin_dir, is_new_plugin):
    errors = []
    version = None

    plugin_file = os.path.join(plugin_dir, 'metadata.yaml')
    if not os.path.isfile(plugin_file):
        errors.append(f"错误：插件 {plugin_dir} 缺少 metadata.yaml 文件")
        return errors, None

    with open(plugin_file) as f:
        plugin = yaml.safe_load(f)

    if not plugin.get('name'):
        errors.append(f"错误：插件 {plugin_dir} 的名称不能为空")

    if not is_new_plugin:  # 如果是历史插件的更新 PR
        version = plugin.get('version')
        if not version:
            errors.append(f"错误：插件 {plugin_dir} 的版本号不能为空")

    return errors, version


def get_changed_plugins(files):
    # 通过检查文件路径，确定受到影响的插件目录
    changed_plugins = set()
    for file in files:
        parts = file.split('/')
        if len(parts) >= 2 and parts[0] == 'plugins':
            changed_plugins.add(parts[1])
    return changed_plugins


def get_current_version(plugin_dir):
    # 使用 Git 命令获取之前的版本号
    command = f"git show HEAD:plugins/{os.path.relpath(plugin_dir, start='plugins')}/metadata.yaml"
    try:
        result = subprocess.check_output(command, shell=True, text=True)
        metadata = yaml.safe_load(result)
        return metadata.get('version')
    except subprocess.CalledProcessError:
        return None
    except yaml.YAMLError:
        return None


def tag_plugin_version(plugin_name, version):
    tag_name = f"{plugin_name}|v{version}"
    existing_tags = subprocess.getoutput('git tag').split('\n')

    if tag_name not in existing_tags:
        subprocess.run(["git", "tag", tag_name])
        print(f"添加标签：{tag_name}")


def main(plugins_dir):
    changed_files = os.getenv('CHANGED_FILES').split() if os.getenv('CHANGED_FILES') else []
    changed_plugins = get_changed_plugins(changed_files)

    errors = []

    for plugin_name in os.listdir(plugins_dir):
        plugin_path = os.path.join(plugins_dir, plugin_name)
        if not os.path.isdir(plugin_path):
            continue

        is_new_plugin = plugin_name in changed_plugins
        plugin_errors, version = check_each_plugin(plugin_path, is_new_plugin)

        if plugin_errors:
            errors.extend(plugin_errors)

        if version:
            tag_plugin_version(plugin_name, version)

    if errors:
        for error in errors:
            print(error)
        sys.exit(1)


if __name__ == '__main__':
    main(os.path.abspath("./plugins"))
