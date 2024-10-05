from __future__ import annotations

def AOV_check(layers_dict: dict) -> dict|None:
    """
     Sanity Check for the read nodes selected that has the correct AOV's needed for the template.

     @layers_dict: dict - Dictionary with the AOV's needed for the template.

     @return Dictionary with the read nodes and AOV's found, if something went wrong None.
    """
    from .nuke_helper import (get_type_nodes, get_layers, create_progress_task, error_messages)
    # Get all the read nodes selected
    read_nodes = get_type_nodes('Read')
    read_data = dict()
    wrong_data = dict()
    # Start progress bar
    task = create_progress_task('Searching for correct AOVs in the read nodes selected')
    progPerRead = 90.0/float(len(read_nodes))
    progress = 10
    for read_node in read_nodes:
        read_node.knob('tile_color').setValue(0)
        missing_layers = list()
        layers_found = dict()
        task.setMessage('Reviewing {}'.format(read_node['name'].value()))
        # Get all AOV's founded in the read node
        found_layers = get_layers(read_node)
        for group, layers in layers_dict.items():
            layers_intersected = list(set(found_layers).intersection(layers))
            # Checks if there is no AOV intersected skip
            if not layers_intersected:
                continue
            # Checks if the AOV's found are not the same as the template needed added to list the missing AOV
            elif not set(layers) == set(layers_intersected):
                missing_layers.extend(list(set(layers).difference(layers_intersected)))
                continue
            layers_found[group] = layers
        # If there are missing AOV's group them with the corresponded read node for future error message
        if missing_layers:
            wrong_data[read_node] = missing_layers
        # If there is no issue added to the dictionary
        else:
            read_data[read_node] = layers_found
        # Progress calculation
        progress = int(progPerRead + progress)
        task.setProgress(progress)
        if task.isCancelled():
            return None
    if wrong_data:
        # Creates an error message for founded missing AOV's 
        error_message = 'There are some missing AOVs\n'
        nuke_hex = int('%02x%02x%02x%02x' % (int(1*255),int(0*255),int(0*255),255),16)
        for read_node, missing_layers in wrong_data.items():
            error_message += '{0} -> {1}\n'.format(read_node['name'].value(), ', '.join(missing_layers))
            read_node.knob('tile_color').setValue(nuke_hex)
        error_messages(error_message)
        return None
    
    return read_data