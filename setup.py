import os

from setuptools import setup, find_packages


# 自动包含两个目录下的所有文件（含非Python文件）
def package_files(directory):
    paths = []
    for (path, _, filenames) in os.walk(directory):
        for filename in filenames:
            paths.append(os.path.join('..', path, filename))
    return paths

# 动态获取lib/process目录下的所有文件
extra_files = []
extra_files += package_files('lib')
extra_files += package_files('process')

setup(
    name="hksdk",
    version="1.0.0",
    author="lining",
    author_email="27919034@qq.com",
    description="使用python调用海康SDK",
    license='MIT',
    py_modules=['hksdk'],
    url='https://github.com/lining808/hksdk',
    install_requires=['numpy', 'opencv-python'],
    # 安装过程中，需要安装的静态文件，如配置文件、service文件、图片等
    packages=['lib', 'process'],  # 手动指定要打包的目录
    package_dir={
        'lib': 'lib',  # 声明lib包的物理路径
        'process': 'process'  # 声明process包的物理路径
    },
    package_data={
        '': ['*.*'],  # 包含所有类型文件
        'lib': extra_files,  # 动态添加的lib文件
        'process': extra_files  # 动态添加的process文件
    },
    include_package_data=True,  # 启用非代码文件包含
)



