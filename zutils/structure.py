# pip install easy-media-zutils
from tree_utils.struct_tree_out import print_tree

path = r'../../myDeepdoc'
exclude_dirs_set = {'using_files', 'zutils', 'rag', 'LICENSE', 'parser', 'data', 'test', 'font', 'from'}
print_tree(directory=path, exclude_dirs=exclude_dirs_set)
