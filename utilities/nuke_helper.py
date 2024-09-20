from __future__ import annotations
import nuke
import nukescripts

def create_group(name: str, seq: int = 1):
    """
     Creates a group node with the name and sequence for the name.

     @name: str - The name for the group node.
     @seq: int - The sequence for the group name by default is 1.

     @return Nuke node
    """
    group_node = nuke.createNode('Group')
    group_node['name'].setValue('{0} Group {1}'.format(name, str(seq)))
    return group_node

def create_input():
    """
     Creates an Input node

     @return Nuke node
    """
    input_node = nuke.createNode('Input')
    return input_node


def create_output():
    """
     Create an Output node

     @return Nuke node
    """
    output_node = nuke.createNode('Output')
    return output_node


def create_mergeExpression(label: str):
    """
     Create a merge node using a expression to divide and break the AOV to generate the Raw Lighting

     @label: str - The name for the merge label

     @return Nuke node
    """
    merge_node = nuke.nodes.MergeExpression()
    merge_node['label'].setValue('Raw {} Lighting'.format(label))
    merge_node['expr0'].setValue('Ar == 0 ? Br : Br/Ar')
    merge_node['expr1'].setValue('Ag == 0 ? Bg : Bg/Ag')
    merge_node['expr2'].setValue('Ab == 0 ? Bb : Bb/Ab')
    merge_node['expr3'].setValue('Aa == 0 ? Ba : Ba/Aa')
    return merge_node


def create_merge(name: str, operation: str):
    """
     Creates a merge node with a specific name and operation.

     @name: str - Name of the node.
     @operation: str - The operation that the merge will do.

     @return Nuke node.
    """
    merge_node = nuke.nodes.Merge2(label='{0}_{1}'.format(name, operation))
    merge_node['operation'].setValue(operation)
    return merge_node


def create_mergePass(name: str):
    """
     Creates a merge node using the name provided with the suffix Pass using the multiply operation.

     @name: str - Name for the label of the node.

     @return Nuke node.
    """
    merge_node = nuke.nodes.Merge2(label='{} Pass'.format(name))
    merge_node['operation'].setValue('multiply')
    return merge_node


def create_remove(layer: str, operation: str='keep', channels: str= 'rgb'):
    """
     Creates a remove node.

     @layer: str - Part of the name of the node.
     @operation: str - The operation that the remove node will do and also for the name of the node.
     @channels: str - The channels that it will use.

     @return Nuke node.
    """
    remove_node = nuke.nodes.Remove(label='{0}_{1}'.format(layer,operation))
    remove_node['operation'].setValue(operation)
    remove_node['channels'].setValue(channels)
    return remove_node


def create_dot(label_txt: str|None = None, font_size: int = 25):
    """
     Creates a dot node.

     @label_txt: str|None - The label that it will show in the dot
     @font_size: int - The size of the font for the label

     @return Nuke node.
    """
    dot_node = nuke.nodes.Dot()
    if label_txt:
        dot_node['label'].setValue(label_txt)
        dot_node['note_font_size'].setValue(font_size)
    return dot_node


def create_copy(from_channels: list[str], to_channels: list[str], node_name: str):
    """
     Create a copy node to get the channels that are going to be copy.

     @from_channels: list[str] - The channels you want to copy from.
     @to_channels: list[str] - The channels you want to copy to.
     @node_name: str - The name of the node.

     @return Nuke node.
    """
    copy_node = nuke.nodes.Copy()
    copy_node['name'].setValue('{}_copy'.format(node_name))
    for index, channel in enumerate(from_channels):
        copy_node['from{}'.format(index)].setValue(channel)
        copy_node['to{}'.format(index)].setValue(to_channels[index])
    return copy_node


def create_premult(name: str):
    """
     Creates a premult node.

     @name: str - The name of the node

     @return Nuke node.
    """
    premult_node = nuke.nodes.Premult()
    premult_node['name'].setValue('{}_Premult'.format(name))
    return premult_node


def create_unpremult(name: str):
    """
     Creates an unpremult node.

     @name: str - The name for the node

     @return Nuke node.
    """
    unpremult_node = nuke.nodes.Unpremult()
    unpremult_node['name'].setValue('{}_Unpremult'.format(name))
    return unpremult_node


def shuffle_aov(layer: str):
    """
     Creates a shuffle node with the specific AOV.

     layer: str - The AOV to be used

     @return Nuke node.
    """
    shuffle_node = nuke.nodes.Shuffle2(label=layer)
    shuffle_node['in1'].setValue(layer)
    shuffle_node['postage_stamp'].setValue( True )
    return shuffle_node


def create_backdrops(width: int, height: int, label: str|None = None, font_size: int|None = None):
    """
     Create a backdrop with the specific width, height, font size and label for it.

     @width: int - The value for the width.
     @height: int - The value for the height.
     @label: str|None - The text to be display in the label.
     @font_size: int - The size of the font to be displayed in the label.

     @return Nuke node.
    """
    backdrop_node = nukescripts.autoBackdrop()
    if label:
        backdrop_node.setName(label)
        backdrop_node['label'].setValue(label)
        backdrop_node['name'].setValue(label)
    if font_size:
        backdrop_node['note_font_size'].setValue(font_size)
    backdrop_node["bdwidth"].setValue(width)
    backdrop_node["bdheight"].setValue(height)
    return backdrop_node


def get_layers(node) -> list[str]:
    """
     Get all the AOV's from a read node.

     @node: Nuke node - The node to look for the AOV's

     @return List of string with all the AOV's founded in the node.
    """
    channels = node.channels()
    layers = list( set([c.split('.')[0] for c in channels]) )
    layers.sort()
    return layers


def get_type_nodes(node_class: str) -> list:
    """
     Get a specific type of nodes from a selection.

     @node_class: str - The type of the node.

     @return List of all selected nodes.
    """
    selected_nodes = nuke.selectedNodes(node_class)
    return selected_nodes


def get_all_groups_names() -> list[str]:
    """
     Search for all the group nodes and get the names.

     @return List of strings with the name of all the group nodes.
    """
    group_names = [node.name() for  node in nuke.allNodes('Group')]
    return group_names


def get_node_by_name(name: str):
    """
     Gets the node in nuke using the name of the node.

     @name: str - The name of the node.

     @return Nuke node.
    """
    node = nuke.toNode(name)
    return node


def create_progress_task(title: str):
    """
     Create a progress bar in Nuke.

     @title: str - The title of the progress bar.

     @return Progress bar.
    """
    return nuke.ProgressTask(title)


def error_messages(message: str, format: str = 'error'):
    """
     Creates a window showing an error.

     @message: str - The message to display.
     @format: str - The type of format that the message will have.

     @return Nuke message with the error.
    """
    if format == 'error':
            errorFormat = '<font color=\"#F71010\"><font size=\"4\">ERROR:</font></font>'
    elif format == 'warning':
        errorFormat = '<font color=\"#F7A610\"><font size=\"4\">WARNING:</font></font>'
    elif format == 'notice':
        errorFormat = '<font color=\"#0573FA\"><font size=\"4\">NOTICE:</font></font>'
    nuke.message(("{} " + message).format(errorFormat))


def deselect_nodes() -> None:
    """
     Deselect all the nodes selected.

     @return None.
    """
    if nuke.selectedNodes():
        for i in nuke.selectedNodes():
            i['selected'].setValue(False)


def select_nodes(nodes_list: list) -> None:
    """
     Make a selection of the list of nodes.

     @nodes_list: list - List of nodes.

     @return None.
    """
    for node in nodes_list:
        node['selected'].setValue(True)


def backdrop_wh_nodes(nodes_enclosed: list) -> tuple:
    """
     Calculate the width and height of a backdrop from a selection of nodes.

     @nodes_enclosed: list - List of nodes.

     @return Tuple the width and height of the backdrop.
    """
    xpos_list = list()
    ypos_list = list()
    for node in nodes_enclosed:
        xpos_list.append(node['xpos'].value())
        ypos_list.append(node['ypos'].value())
    width = max(xpos_list) - min(xpos_list) + 99
    height = max(ypos_list) - min(ypos_list) + 115
    return width, height


def backdrop_wh_backdrops(selected_backdrops: list) -> tuple:
    """
     Calculate the width and height of a backdrop from a selection of backdrops.

     @selected_backdrops: list - List of backdrop nodes.

     @return Tuple the width and height of the backdrop.
    """
    xpos_list = list()
    ypos_list = list()
    bdwidth_list = list()
    bdheight_list = list()
    for node in selected_backdrops:
        xpos_list.append(node['xpos'].value())
        ypos_list.append(node['ypos'].value())
        bdwidth_list.append(node['bdwidth'].value())
        bdheight_list.append(node['bdheight'].value())
    width = max(xpos_list) - min(xpos_list) + 120
    height = max(ypos_list) - min(ypos_list)
    if width == 120:
        width = max(bdwidth_list) + 120
    if not height:
        height = max(bdheight_list) + 85
    return width, height


def delete_node(node) -> None:
    """
     Delete the node selected.

     @return None.
    """
    nuke.delete(node)

