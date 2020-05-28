import h5py


def _report(operation, key, obj, log_file):
    type_str = type(obj).__name__.split(".")[-1].lower()
    log_file.write("%s %s: %s, %s\n" % (operation, type_str, key, obj))


def copy_attributes(in_object, out_object):
    '''
    Copy attributes between 2 HDF5 objects.
    '''
    for key, value in in_object.attrs.items():
        out_object.attrs[key] = value


def copy_hdf5_obj(in_object, out_object, layer_pairs):
    for key, in_obj in in_object.items():
        if isinstance(in_obj, h5py.Group):
            out_obj = out_object.create_group(key)
            copy_hdf5_obj(in_obj, out_obj, layer_pairs)
        elif isinstance(in_obj, h5py.Dataset):
            out_object.create_dataset(key, data=in_obj)
        else:
            print("non-understandable ", key, in_obj)
            in_obj.copy(key, out_object)
    copy_attributes(in_object, out_object, layer_pairs)


def edit_hdf5_obj(in_object, out_object, layer_pairs):
    for key, out_obj in out_object.items():
        if isinstance(out_obj, h5py.Group):
            if key in in_object:
                edit_hdf5_obj(in_object[key], out_object[key], layer_pairs)
            elif key in layer_pairs:
                edit_hdf5_obj(in_object[layer_pairs[key]], out_object[key], layer_pairs)
        elif isinstance(out_obj, h5py.Dataset):
            if key in in_object:
                out_object[key] = in_object[key]
            elif key in layer_pairs:
                out_object[key] = in_object[layer_pairs[key]]


def visit_hdf5_file(in_file, log_file):
    for key, in_obj in in_file.items():
        _report('item', key, in_obj, log_file)
        if isinstance(in_obj, h5py.Group):
            visit_hdf5_file(in_obj, log_file)
    for key, value in in_file.attrs.items():
        _report('attr', key, value, log_file)


def copy_weights(src_filepath, dest_filepath, layer_pairs):
    # with h5py.File(src_filepath, 'r') as in_file, h5py.File(dest_filepath, 'a') as out_file:
    #     edit_hdf5_obj(in_file, out_file, layer_pairs)

    with h5py.File(src_filepath, 'r') as in_file, open('%s.txt' % src_filepath, 'w') as log_file:
        visit_hdf5_file(in_file, log_file)

    # with h5py.File(dest_filepath, 'r') as in_file, open('%s.txt' % dest_filepath, 'w') as log_file:
    #     visit_hdf5_file(in_file, log_file)


if __name__ == '__main__':
    layer_pairs = {}
    src_filepath = '/home/mechmind021/3d_data/weights/rgbd_models/model-ep001-loss7.144-val_loss7.359.h5'
    dest_filepath = '/home/mechmind021/3d_data/weights/mask_rcnn_coco_0001.h5'
    copy_weights(src_filepath, dest_filepath, layer_pairs)
