from __future__ import annotations

def run_create(template_type: str, new_group: bool) -> None:
    """
     Separates all the AOVs using the template type selected to review or apply corrections if needed.

     @param template_type: str - Name of the template selected.
     @param new_group: bool - True to create a new group node, False deletes and create the original.

     @return None.
    """
    from .nuke_helper import (create_progress_task)
    from .sanity_check import (AOV_check)
    # Looks for the template needed
    layers_dict = template_selection(template_type)
    # Do a sanity check in the selected Read nodes for the AOV's needed
    read_data = AOV_check(layers_dict)
    # Ends if there was an error in the Read nodes
    if not read_data:
        return
    # Calculates the progress bar for the selected Read nodes
    progPerRead = 90.0/float(len(read_data))
    progress = 10
    # Builds the template and starts the progress bar
    for read_node, layers_found in read_data.items():
        task = create_progress_task('Building {} Template'.format(template_type))
        build_up(layers_found, read_node, task, new_group)
        progress = int(progPerRead + progress)
        task.setProgress(progress)
        if task.isCancelled():
            return


def template_selection(template_type: str) -> dict:
    """
     Get's the dictionary needed to create the template.
     
     @template_type: str - Name of the template selected.

     @return Dictionary with the AOV's needed for the template.
    """
    if template_type == 'Simple':
        layers_dict = {'General': ['direct', 'albedo', 'indirect'],
                       'Emission':['emission'],
                       'Shadow':['shadow_matte']}
    elif template_type == 'Intermediate':
        layers_dict = {'Diffuse': ['diffuse', 'diffuse_albedo'],
                       'SSS':['sss', 'sss_albedo'],
                       'Transmission':['transmission', 'transmission_albedo'],
                       'Specular':['specular', 'specular_albedo'],
                       'Coat':['coat', 'coat_albedo'],
                       'Sheen':['sheen', 'sheen_albedo'],
                       'Emission':['emission'],
                       'Shadow':['shadow_matte']}
    elif template_type == 'Complex':
        layers_dict = {'Diffuse': ['diffuse_direct', 'diffuse_albedo', 'diffuse_indirect'],
                       'SSS':['sss_direct', 'sss_albedo', 'sss_indirect'],
                       'Transmission':['transmission_direct', 'transmission_albedo', 'transmission_indirect'],
                       'Specular':['specular_direct', 'specular_albedo', 'specular_indirect'],
                       'Coat':['coat_direct', 'coat_albedo', 'coat_indirect'],
                       'Sheen':['sheen_direct', 'sheen_albedo', 'sheen_indirect'],
                       'Emission':['emission'],
                       'Shadow':['shadow_matte']}
    return layers_dict


def build_up(layers_dict: dict, read_node, progress_bar, new_group: bool) -> None:
    """
     Wrapper to start building the template with a group or in direct in the workspace.

     @layers_dict: dict - A dictionary that contains all the AOV's in groups.
     @read_node: Nuke Node - A read node from nuke, to get specific information.
     @progress_bar: Progress Bar - Progress bar created in Nuke to update messages.
     @new_group: bool - True to create a new group node, False deletes and create the original.

     @return None.
    """
    from .nuke_helper import (create_group, create_input, create_output, get_all_groups_names)
    # Verify for group nodes that has similar names to delete or create a new one
    if new_group:
        build_group(layers_dict, read_node, progress_bar)
    else:
        node = build_comp(layers_dict, read_node, progress_bar)


def build_group(layers_dict: dict, read_node, progress_bar) -> None:
    """
     Start building the template inside the group.

     @layers_dict: dict - A dictionary that contains all the AOV's in groups.
     @read_node: Nuke Node - A read node from nuke, to get specific information.
     @progress_bar: Progress Bar - Progress bar created in Nuke to update messages.

     @return None.
    """
    from .nuke_helper import (create_group, create_input, create_output, get_all_groups_names)
    group_names = get_all_groups_names()
    next_seq = 1
    seq_group = [int(group_name.split(' ')[-1]) for group_name in group_names if read_node['name'].value() in group_name]
    if seq_group:
        next_seq = max(seq_group) + 1
    group_node = create_group(read_node['name'].value(), next_seq)
    # Starts creating the template inside the group
    with group_node:
        input_node = create_input()
        # Set the position of the input, to go around the bug of not setting the template correctly
        input_node['xpos'].setValue(0)
        input_node['ypos'].setValue(0)
        # Start building comp
        last_node = build_comp(layers_dict, read_node, progress_bar, input_node)
        # Creates the Output
        output_node = create_output()
        output_node.setInput(0, last_node)
        output_node['xpos'].setValue(last_node['xpos'].value())
        output_node['ypos'].setValue(last_node['ypos'].value()+50)
    # Set the group node position
    group_node.setInput(0, read_node)
    group_node['xpos'].setValue(read_node['xpos'].value())
    group_node['ypos'].setValue(read_node['ypos'].value()+100)

def build_comp(layers_dict: dict, read_node, progress_bar, input_node = None) -> None:
    """
     Start building the template with the selected options.

     @layers_dict: dict - A dictionary that contains all the AOV's in groups.
     @read_node: Nuke Node - A read node from nuke, to get specific information.
     @progress_bar: Progress Bar - Progress bar created in Nuke to update messages.
     @input_node: Node|None -Default value as None if there is no input node and uses the read node otherwise uses the input node given.

     @return None.
    """
    if not input_node:
        input_node = read_node
    # Set the first node of the template an unpremult
    progress_bar.setMessage('Creating the unpremult')
    unpremult_node = build_unpremult(input_node, read_node['name'].value())
    # Start building all the AOV's found for the template
    progress_bar.setMessage('Building the AOVs')
    passes_merge, emission_node = build_layers(layers_dict, unpremult_node)
    # Creates all the merges from all the passes to get the beauty again
    progress_bar.setMessage('Building the beauty')
    last_merge = build_beauty(passes_merge, emission_node)
    # Copy the alpha from the original render
    progress_bar.setMessage('Copying the alpha')
    copy_node, dot_node = build_copy_alpha(unpremult_node, last_merge, read_node)
    shadow_node = build_shadow_matte(layers_dict, copy_node, dot_node, read_node)
    last_node = build_premult(shadow_node, read_node)
    return last_node

def build_unpremult(start_node, name: str):
    """
     Builds the unpremult node to start the template.

     @start_node: Nuke node - Node used to get the position and start building from there.
     @name: str - The name for the unpremult node.

     @return A Nuke node the Unpremult Node.
    """
    from .nuke_helper import (create_unpremult)
    start_pos_x = start_node['xpos'].value()
    start_pos_y = start_node['ypos'].value()
    unpremult_node = create_unpremult(name)
    unpremult_node.setInput(0, start_node)
    unpremult_node['xpos'].setValue(start_pos_x)
    unpremult_node['ypos'].setValue(start_pos_y+90)
    return unpremult_node


def build_layers(layers_dict: dict, top_node):
    """
     Builds all the AOV's in columns using backdrops to separate each AOV and Group.

     @layers_dict: dict - All the AOV's needed to recreate the beauty separated in groups.
     @top_node: Nuke node - The starting position where the tree is going to be connected.

     @return Tuple with all the merges that recreates the passes and the emission node that has the emission AOV or None.
    """
    from .nuke_helper import (deselect_nodes, select_nodes, create_backdrops, backdrop_wh_backdrops)
    # Dot offset to start building the tree of the AOVs
    dot_layers_offset_x = 34
    dot_layers_offset_y = 90
    emission_node = None
    passes_merge = list()
    # Loop through all the groups and layers needed
    for group, layers in layers_dict.items():
        all_merge_nodes = list()
        backdrop_layers = list()
        if 'Shadow' in group:
            continue
        for layer in layers:
            # Deselects nodes to prevent not wanted connections
            deselect_nodes()
            # Look for specific names in the layers to give a different function
            if 'albedo' in layer:
                top_node, dot_albedo_nodes, backdrop_node = build_albedo(top_node, layer, dot_layers_offset_x, dot_layers_offset_y)
                backdrop_layers.append(backdrop_node)
            elif 'emission' in layer:
                emission_node, backdrop_node = build_emission(top_node, layer, dot_layers_offset_x, dot_layers_offset_y)
                backdrop_layers.append(backdrop_node)
            else:
                top_node, merge_nodes, backdrop_node = build_aov(top_node, layer, dot_layers_offset_x, dot_layers_offset_y)
                all_merge_nodes.extend(merge_nodes)
                backdrop_layers.append(backdrop_node)
            # Create a new offset for the dots that connects
            dot_layers_offset_x = backdrop_node['bdwidth'].value() + 50
            dot_layers_offset_y = 0
        # Connects all the merges to get the global lighting for comp and recreate the AOV
        for merge_node in all_merge_nodes:
            if 'Lighting' in merge_node['label'].value():
                merge_node.setInput(1, dot_albedo_nodes[0])
            elif 'Pass' in merge_node['label'].value():
                merge_node.setInput(1, dot_albedo_nodes[1])
                passes_merge.append(merge_node)
        # Selects the backdrops of the layers to create a new backdrop with the group it belongs
        select_nodes(backdrop_layers)
        width, height = backdrop_wh_backdrops(backdrop_layers)
        group_backdrop = create_backdrops(width=width, height=height, label=group)
    return passes_merge, emission_node


def build_beauty(passes_merge: list, emission_node):
    """
     Connects all the AOV's merge to recreate the beauty.

     @passes_merge: list - List that contains all the merge nodes of the AOV's.
     @emission_node: Nuke Node|None - Contains the last emission node to recreate the beauty or None if there is no emission.

     @return A Nuke node the last merge node created.
    """
    from .nuke_helper import (create_dot, create_merge)
    last_merge = passes_merge[0]
    index = 1
    # Loops through all the AOV's merge to recreate the beauty
    while index < len(passes_merge):
        pass_name = passes_merge[index]['label'].value().split(" ")[0]
        merge_node = create_merge(pass_name, 'plus')
        dot_node = create_dot(pass_name)
        merge_node['xpos'].setValue(last_merge['xpos'].value())
        merge_node['ypos'].setValue(last_merge['ypos'].value()+80)
        dot_node['xpos'].setValue(passes_merge[index]['xpos'].value()+34)
        dot_node['ypos'].setValue(merge_node['ypos'].value()+9)
        merge_node.setInput(0, last_merge)
        merge_node.setInput(1, dot_node)
        dot_node.setInput(0, passes_merge[index])
        last_merge = merge_node
        index += 1
    # Checks if the emission node is needed to complete the beauty
    if emission_node:
        dot_emission = create_dot('emission')
        dot_emission.setInput(0, emission_node)
        emission_merge = create_merge('emission', 'plus')
        emission_merge.setInput(0, last_merge)
        emission_merge.setInput(1, dot_emission)
        emission_merge['xpos'].setValue(last_merge['xpos'].value())
        emission_merge['ypos'].setValue(last_merge['ypos'].value()+60)
        dot_emission['xpos'].setValue(emission_node['xpos'].value()+34)
        dot_emission['ypos'].setValue(emission_merge['ypos'].value()+9)
        last_merge = emission_merge
    return last_merge


def build_copy_alpha(unpremult_node, last_merge, read_node):
    """
     Builds the last part of the template copying the alpha from the original to the recreated beauty.

     @unpremult_node: Nuke node - The node where it is going to copy the alpha.
     @last_merge: Nuke node - The last merge node of the AOV's to paste the alpha.
     @read_node: Nuke node - The read node to use the name.

     @return A Nuke node the unpremult node
    """
    from .nuke_helper import (create_dot, create_copy)
    dot_copy_1 = create_dot()
    dot_copy_1.setInput(0, unpremult_node)
    dot_copy_1['xpos'].setValue(unpremult_node['xpos'].value()-120)
    dot_copy_1['ypos'].setValue(unpremult_node['ypos'].value()+3)
    dot_copy_2 = create_dot()
    dot_copy_2.setInput(0, dot_copy_1)
    dot_copy_2['xpos'].setValue(dot_copy_1['xpos'].value())
    dot_copy_2['ypos'].setValue(last_merge['ypos'].value()+68)
    copy_node = create_copy(from_channels=['rgba.alpha'], to_channels=['rgba.alpha'], node_name=read_node['name'].value())
    copy_node.setInput(0, last_merge)
    copy_node.setInput(1, dot_copy_2)
    copy_node['xpos'].setValue(dot_copy_2['xpos'].value()+120)
    copy_node['ypos'].setValue(last_merge['ypos'].value()+60)
    return copy_node, dot_copy_2


def build_shadow_matte(layers_dict: dict, top_node, dot_node, read_node):
    """
     Build the tree for the Shadow Matte AOV.

     @layers_dict: dict - Dictionary with all the layers founded in the read node.
     @top_node: Nuke node - The starting node to connect the grade.
     @dot_node: Nuke node - The dot node to get the Shadow AOV.
     @read_node: Nuke node - The original read node to get the name.

     @return Nuke Node.
    """
    from .nuke_helper import (shuffle_aov, select_nodes, create_backdrops, backdrop_wh_nodes, create_grade, deselect_nodes)
    deselect_nodes()
    if not layers_dict.get('Shadow'):
        return top_node
    layer = layers_dict.get('Shadow')
    shuffle_node = shuffle_aov(layer[0])
    shuffle_node.setInput(0, dot_node)
    shuffle_node['xpos'].setValue(dot_node['xpos'].value()-34)
    shuffle_node['ypos'].setValue(dot_node['ypos'].value()+130)
    shuffle_node["mappings"].setValue('shadow_matte.red', 'rgba.alpha')
    grade_node = create_grade(read_node['name'].value())
    grade_node.setInput(0, top_node)
    grade_node.setInput(grade_node.minInputs()-1, shuffle_node)
    grade_node['xpos'].setValue(top_node['xpos'].value())
    grade_node['ypos'].setValue(top_node['ypos'].value()+168)
    nodes_to_select = [shuffle_node, grade_node]
    select_nodes(nodes_to_select)
    width, height = backdrop_wh_nodes(nodes_to_select)
    backdrop_node = create_backdrops(width, height, 'Shadow')
    return grade_node
    

def build_premult(top_node, read_node):
    """
     Build the tree to break the AOV.

     @top_node: Nuke node - A nuke node to get the position to start building.
     @read_node: str - The original read node to get the name.

     @return Nuke Node.
    """
    from .nuke_helper import (create_premult, deselect_nodes)
    premult_node = create_premult(read_node['name'].value())
    premult_node.setInput(0, top_node)
    premult_node['xpos'].setValue(top_node['xpos'].value())
    premult_node['ypos'].setValue(top_node['ypos'].value()+120)
    deselect_nodes()
    return premult_node


def build_aov(node_to_connect, layer: str, x_offset: int, y_offset: int):
    """
     Build the tree to break the AOV.

     @node_to_connect: Nuke node - A nuke node to get the position to start building.
     @layer: str - The name of the AOV to rename the nodes.
     @x_offset: int - Offset in X for the dot node.
     @ y_offset: int - Offset in Y for the dot node.

     @return Tuple dot node to get the top position, merge nodes to break the AOV for the global lighting and recreate, backdrop node to create the group backdrop.
    """
    from .nuke_helper import (create_dot, shuffle_aov, create_remove, create_mergeExpression,
                          create_mergePass, select_nodes, create_backdrops, backdrop_wh_nodes)
    dot_node = create_dot()
    dot_node.setInput(0, node_to_connect)
    dot_node['xpos'].setValue(node_to_connect['xpos'].value()+x_offset)
    dot_node['ypos'].setValue(node_to_connect['ypos'].value()+y_offset)
    # Creates a shuffle to get the AOV
    shuffle_node = shuffle_aov(layer)
    shuffle_node.setInput(0, dot_node)
    shuffle_node['xpos'].setValue(dot_node['xpos'].value()-34)
    shuffle_node['ypos'].setValue(dot_node['ypos'].value()+180)
    # Create a remove node to delete other layers and just get the specific AOV
    remove_node = create_remove(layer)
    remove_node.setInput(0, shuffle_node)
    remove_node['xpos'].setValue(shuffle_node['xpos'].value())
    remove_node['ypos'].setValue(shuffle_node['ypos'].value()+100)
    # Merge to get the global lighting
    merge_expression_node = create_mergeExpression(layer)
    merge_expression_node.setInput(0, remove_node)
    merge_expression_node['xpos'].setValue(remove_node['xpos'].value())
    merge_expression_node['ypos'].setValue(remove_node['ypos'].value()+70)
    # Merge to rebuild the AOV
    merge_node = create_mergePass(layer)
    merge_node.setInput(0, merge_expression_node)
    merge_node['xpos'].setValue(merge_expression_node['xpos'].value())
    merge_node['ypos'].setValue(merge_expression_node['ypos'].value()+400)
    # Select node to create the backdrop and get the width and height
    nodes_to_select = [shuffle_node, remove_node, merge_expression_node, merge_node]
    select_nodes(nodes_to_select)
    width, height = backdrop_wh_nodes(nodes_to_select)
    backdrop_node = create_backdrops(width=width+200, height=height, label=layer, font_size=25)
    # List of the merge nodes for connection with the albedo
    merge_nodes = [merge_expression_node, merge_node]
    return dot_node, merge_nodes, backdrop_node


def build_albedo(node_to_connect, layer:str, x_offset: int, y_offset: int):
    """
     Build the tree for the albedo AOV.

     @node_to_connect: Nuke node - A nuke node to get the position to start building.
     @layer: str - The name of the AOV to rename the nodes.
     @x_offset: int - Offset in X for the dot node.
     @ y_offset: int - Offset in Y for the dot node.

     @return Tuple dot node to get the top position, dot albedo nodes to connect to the merge to break and recreate the AOV, backdrop node to create the group backdrop.
    """
    from .nuke_helper import (create_dot, shuffle_aov, create_remove, select_nodes, create_backdrops, backdrop_wh_nodes)
    dot_node = create_dot()
    dot_node.setInput(0, node_to_connect)
    dot_node['xpos'].setValue(node_to_connect['xpos'].value()+x_offset)
    dot_node['ypos'].setValue(node_to_connect['ypos'].value()+y_offset)
    # Creates a shuffle to get the AOV
    shuffle_node = shuffle_aov(layer)
    shuffle_node.setInput(0, dot_node)
    shuffle_node['xpos'].setValue(dot_node['xpos'].value()-34)
    shuffle_node['ypos'].setValue(dot_node['ypos'].value()+180)
    # Create a remove node to delete other layers and just get the specific AOV
    remove_node = create_remove(layer)
    remove_node.setInput(0, shuffle_node)
    remove_node['xpos'].setValue(shuffle_node['xpos'].value())
    remove_node['ypos'].setValue(shuffle_node['ypos'].value()+100)
    # Create a dot for the global lighting
    dot_expression_node = create_dot()
    dot_expression_node.setInput(0, remove_node)
    dot_expression_node['xpos'].setValue(remove_node['xpos'].value()+34)
    dot_expression_node['ypos'].setValue(remove_node['ypos'].value()+79)
    # Create a dot to rebuild the AOV
    dot_merge_node = create_dot()
    dot_merge_node.setInput(0, dot_expression_node)
    dot_merge_node['xpos'].setValue(dot_expression_node['xpos'].value())
    dot_merge_node['ypos'].setValue(dot_expression_node['ypos'].value()+400)
    # Select node to create the backdrop and get the width and height
    nodes_to_select = [shuffle_node, remove_node, dot_expression_node, dot_merge_node]
    select_nodes(nodes_to_select)
    width, height = backdrop_wh_nodes(nodes_to_select)
    backdrop_node = create_backdrops(width=width, height=height, label=layer, font_size=25)
    # List of the dot nodes for connection with the other AOV's
    dot_albedo_nodes = [dot_expression_node, dot_merge_node]
    return dot_node, dot_albedo_nodes, backdrop_node


def build_emission(node_to_connect, layer:str, x_offset: int, y_offset: int):
    """
     Build the tree for the emission AOV.

     @node_to_connect: Nuke node - A nuke node to get the position to start building.
     @layer: str - The name of the AOV to rename the nodes.
     @x_offset: int - Offset in X for the dot node.
     @ y_offset: int - Offset in Y for the dot node.

     @return Tuple remove node to get the position of the last node for emission, backdrop node to create the group backdrop.
    """
    from .nuke_helper import (create_dot, shuffle_aov, create_remove, select_nodes, create_backdrops, backdrop_wh_nodes)
    dot_node = create_dot()
    dot_node.setInput(0, node_to_connect)
    dot_node['xpos'].setValue(node_to_connect['xpos'].value()+x_offset)
    dot_node['ypos'].setValue(node_to_connect['ypos'].value()+y_offset)
    # Creates a shuffle to get the AOV
    shuffle_node = shuffle_aov(layer)
    shuffle_node.setInput(0, dot_node)
    shuffle_node['xpos'].setValue(dot_node['xpos'].value()-34)
    shuffle_node['ypos'].setValue(dot_node['ypos'].value()+180)
    # Create a remove node to delete other layers and just get the specific AOV
    remove_node = create_remove(layer)
    remove_node.setInput(0, shuffle_node)
    remove_node['xpos'].setValue(shuffle_node['xpos'].value())
    remove_node['ypos'].setValue(shuffle_node['ypos'].value()+100)
    # Select node to create the backdrop and get the width and height
    nodes_to_select = [shuffle_node, remove_node]
    select_nodes(nodes_to_select)
    width, height = backdrop_wh_nodes(nodes_to_select)
    backdrop_node = create_backdrops(width=width, height=height, label=layer, font_size=25)
    return remove_node, backdrop_node

