#!/usr/bin/env python3
"""
依赖检查脚本 - 验证新依赖是否符合白名单制度
"""

import sys
import json
import subprocess
from pathlib import Path
from typing import Dict, List, Set


def load_manifest() -> Dict:
    """加载项目配置"""
    manifest_path = Path(__file__).parent.parent / "manifest.json"
    with open(manifest_path, 'r', encoding='utf-8') as f:
        return json.load(f)


def get_package_info(package_name: str) -> Dict[str, str]:
    """获取包信息"""
    try:
        # 使用pip show获取包信息
        result = subprocess.run(
            ['pip', 'show', package_name],
            capture_output=True,
            text=True,
            check=True
        )
        
        info = {}
        for line in result.stdout.split('\n'):
            if ':' in line:
                key, value = line.split(':', 1)
                info[key.strip()] = value.strip()
        
        return info
    except subprocess.CalledProcessError:
        return {}


def check_dependency(package_name: str) -> Dict[str, any]:
    """检查依赖是否符合要求"""
    manifest = load_manifest()
    allowed_deps = manifest.get('allowed_deps', [])
    
    result = {
        'package': package_name,
        'allowed': False,
        'reason': '',
        'info': {}
    }
    
    # 检查是否在白名单中
    if package_name in allowed_deps:
        result['allowed'] = True
        result['reason'] = '在白名单中'
        result['info'] = get_package_info(package_name)
        return result
    
    # 检查包信息
    package_info = get_package_info(package_name)
    result['info'] = package_info
    
    if package_info:
        version = package_info.get('Version', 'unknown')
        result['reason'] = f'不在白名单中 (当前版本: {version})'
    else:
        result['reason'] = '包未安装或不存在'
    
    return result


def main() -> None:
    """主函数"""
    if len(sys.argv) < 2:
        print("使用方法: python scripts/check_dep.py <package_name>")
        print("\n白名单依赖:")
        manifest = load_manifest()
        allowed_deps = manifest.get('allowed_deps', [])
        for dep in sorted(allowed_deps):
            print(f"  - {dep}")
        sys.exit(1)
    
    package_name = sys.argv[1]
    
    print(f"检查依赖: {package_name}")
    print("=" * 50)
    
    result = check_dependency(package_name)
    
    if result['allowed']:
        print(f"✅ {result['package']} - {result['reason']}")
        
        info = result['info']
        if info:
            print(f"   版本: {info.get('Version', 'N/A')}")
            print(f"   位置: {info.get('Location', 'N/A')}")
    else:
        print(f"❌ {result['package']} - {result['reason']}")
        
        print("\n添加依赖到白名单的步骤:")
        print("1. 在 README 中说明用途和收益")
        print("2. 编辑 manifest.json 将依赖加入 allowed_deps")
        print("3. 运行 pip-compile 生成 requirements-lock.txt")
        print("4. 确保 CI 绿灯后方可合并")
    
    # 显示详细的依赖信息
    info = result['info']
    if info and info.get('Required-by'):
        print(f"\n被以下包依赖:")
        for req in info['Required-by'].split(','):
            req = req.strip()
            if req:
                print(f"  - {req}")
    
    # 返回适当的退出码
    sys.exit(0 if result['allowed'] else 1)


if __name__ == "__main__":
    main()