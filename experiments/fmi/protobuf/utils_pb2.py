# Generated by the protocol buffer compiler.  DO NOT EDIT!
# source: protobuf/utils.proto

import sys
_b=sys.version_info[0]<3 and (lambda x:x) or (lambda x:x.encode('latin1'))
from google.protobuf import descriptor as _descriptor
from google.protobuf import message as _message
from google.protobuf import reflection as _reflection
from google.protobuf import symbol_database as _symbol_database
# @@protoc_insertion_point(imports)

_sym_db = _symbol_database.Default()




DESCRIPTOR = _descriptor.FileDescriptor(
  name='protobuf/utils.proto',
  package='dti',
  syntax='proto3',
  serialized_options=_b('P\001'),
  serialized_pb=_b('\n\x14protobuf/utils.proto\x12\x03\x64ti\"\x18\n\x07MString\x12\r\n\x05value\x18\x01 \x01(\t\"\x15\n\x04MU32\x12\r\n\x05value\x18\x01 \x01(\r\"\x15\n\x04MU64\x12\r\n\x05value\x18\x01 \x01(\x04\"\x15\n\x04MI32\x12\r\n\x05value\x18\x01 \x01(\x05\"\x15\n\x04MI64\x12\r\n\x05value\x18\x01 \x01(\x03\"\x15\n\x04MF32\x12\r\n\x05value\x18\x01 \x01(\x02\"\x15\n\x04MF64\x12\r\n\x05value\x18\x01 \x01(\x01\"\x17\n\x06MBytes\x12\r\n\x05value\x18\x01 \x01(\x0c\"l\n\tMNumber32\x12\x1b\n\x06\x66value\x18\x01 \x01(\x0b\x32\t.dti.MF32H\x00\x12\x1b\n\x06uvalue\x18\x02 \x01(\x0b\x32\t.dti.MU32H\x00\x12\x1b\n\x06ivalue\x18\x03 \x01(\x0b\x32\t.dti.MI32H\x00\x42\x08\n\x06number\"l\n\tMNumber64\x12\x1b\n\x06\x66value\x18\x01 \x01(\x0b\x32\t.dti.MF64H\x00\x12\x1b\n\x06uvalue\x18\x02 \x01(\x0b\x32\t.dti.MU64H\x00\x12\x1b\n\x06ivalue\x18\x03 \x01(\x0b\x32\t.dti.MI64H\x00\x42\x08\n\x06numberB\x02P\x01\x62\x06proto3')
)




_MSTRING = _descriptor.Descriptor(
  name='MString',
  full_name='dti.MString',
  filename=None,
  file=DESCRIPTOR,
  containing_type=None,
  fields=[
    _descriptor.FieldDescriptor(
      name='value', full_name='dti.MString.value', index=0,
      number=1, type=9, cpp_type=9, label=1,
      has_default_value=False, default_value=_b("").decode('utf-8'),
      message_type=None, enum_type=None, containing_type=None,
      is_extension=False, extension_scope=None,
      serialized_options=None, file=DESCRIPTOR),
  ],
  extensions=[
  ],
  nested_types=[],
  enum_types=[
  ],
  serialized_options=None,
  is_extendable=False,
  syntax='proto3',
  extension_ranges=[],
  oneofs=[
  ],
  serialized_start=29,
  serialized_end=53,
)


_MU32 = _descriptor.Descriptor(
  name='MU32',
  full_name='dti.MU32',
  filename=None,
  file=DESCRIPTOR,
  containing_type=None,
  fields=[
    _descriptor.FieldDescriptor(
      name='value', full_name='dti.MU32.value', index=0,
      number=1, type=13, cpp_type=3, label=1,
      has_default_value=False, default_value=0,
      message_type=None, enum_type=None, containing_type=None,
      is_extension=False, extension_scope=None,
      serialized_options=None, file=DESCRIPTOR),
  ],
  extensions=[
  ],
  nested_types=[],
  enum_types=[
  ],
  serialized_options=None,
  is_extendable=False,
  syntax='proto3',
  extension_ranges=[],
  oneofs=[
  ],
  serialized_start=55,
  serialized_end=76,
)


_MU64 = _descriptor.Descriptor(
  name='MU64',
  full_name='dti.MU64',
  filename=None,
  file=DESCRIPTOR,
  containing_type=None,
  fields=[
    _descriptor.FieldDescriptor(
      name='value', full_name='dti.MU64.value', index=0,
      number=1, type=4, cpp_type=4, label=1,
      has_default_value=False, default_value=0,
      message_type=None, enum_type=None, containing_type=None,
      is_extension=False, extension_scope=None,
      serialized_options=None, file=DESCRIPTOR),
  ],
  extensions=[
  ],
  nested_types=[],
  enum_types=[
  ],
  serialized_options=None,
  is_extendable=False,
  syntax='proto3',
  extension_ranges=[],
  oneofs=[
  ],
  serialized_start=78,
  serialized_end=99,
)


_MI32 = _descriptor.Descriptor(
  name='MI32',
  full_name='dti.MI32',
  filename=None,
  file=DESCRIPTOR,
  containing_type=None,
  fields=[
    _descriptor.FieldDescriptor(
      name='value', full_name='dti.MI32.value', index=0,
      number=1, type=5, cpp_type=1, label=1,
      has_default_value=False, default_value=0,
      message_type=None, enum_type=None, containing_type=None,
      is_extension=False, extension_scope=None,
      serialized_options=None, file=DESCRIPTOR),
  ],
  extensions=[
  ],
  nested_types=[],
  enum_types=[
  ],
  serialized_options=None,
  is_extendable=False,
  syntax='proto3',
  extension_ranges=[],
  oneofs=[
  ],
  serialized_start=101,
  serialized_end=122,
)


_MI64 = _descriptor.Descriptor(
  name='MI64',
  full_name='dti.MI64',
  filename=None,
  file=DESCRIPTOR,
  containing_type=None,
  fields=[
    _descriptor.FieldDescriptor(
      name='value', full_name='dti.MI64.value', index=0,
      number=1, type=3, cpp_type=2, label=1,
      has_default_value=False, default_value=0,
      message_type=None, enum_type=None, containing_type=None,
      is_extension=False, extension_scope=None,
      serialized_options=None, file=DESCRIPTOR),
  ],
  extensions=[
  ],
  nested_types=[],
  enum_types=[
  ],
  serialized_options=None,
  is_extendable=False,
  syntax='proto3',
  extension_ranges=[],
  oneofs=[
  ],
  serialized_start=124,
  serialized_end=145,
)


_MF32 = _descriptor.Descriptor(
  name='MF32',
  full_name='dti.MF32',
  filename=None,
  file=DESCRIPTOR,
  containing_type=None,
  fields=[
    _descriptor.FieldDescriptor(
      name='value', full_name='dti.MF32.value', index=0,
      number=1, type=2, cpp_type=6, label=1,
      has_default_value=False, default_value=float(0),
      message_type=None, enum_type=None, containing_type=None,
      is_extension=False, extension_scope=None,
      serialized_options=None, file=DESCRIPTOR),
  ],
  extensions=[
  ],
  nested_types=[],
  enum_types=[
  ],
  serialized_options=None,
  is_extendable=False,
  syntax='proto3',
  extension_ranges=[],
  oneofs=[
  ],
  serialized_start=147,
  serialized_end=168,
)


_MF64 = _descriptor.Descriptor(
  name='MF64',
  full_name='dti.MF64',
  filename=None,
  file=DESCRIPTOR,
  containing_type=None,
  fields=[
    _descriptor.FieldDescriptor(
      name='value', full_name='dti.MF64.value', index=0,
      number=1, type=1, cpp_type=5, label=1,
      has_default_value=False, default_value=float(0),
      message_type=None, enum_type=None, containing_type=None,
      is_extension=False, extension_scope=None,
      serialized_options=None, file=DESCRIPTOR),
  ],
  extensions=[
  ],
  nested_types=[],
  enum_types=[
  ],
  serialized_options=None,
  is_extendable=False,
  syntax='proto3',
  extension_ranges=[],
  oneofs=[
  ],
  serialized_start=170,
  serialized_end=191,
)


_MBYTES = _descriptor.Descriptor(
  name='MBytes',
  full_name='dti.MBytes',
  filename=None,
  file=DESCRIPTOR,
  containing_type=None,
  fields=[
    _descriptor.FieldDescriptor(
      name='value', full_name='dti.MBytes.value', index=0,
      number=1, type=12, cpp_type=9, label=1,
      has_default_value=False, default_value=_b(""),
      message_type=None, enum_type=None, containing_type=None,
      is_extension=False, extension_scope=None,
      serialized_options=None, file=DESCRIPTOR),
  ],
  extensions=[
  ],
  nested_types=[],
  enum_types=[
  ],
  serialized_options=None,
  is_extendable=False,
  syntax='proto3',
  extension_ranges=[],
  oneofs=[
  ],
  serialized_start=193,
  serialized_end=216,
)


_MNUMBER32 = _descriptor.Descriptor(
  name='MNumber32',
  full_name='dti.MNumber32',
  filename=None,
  file=DESCRIPTOR,
  containing_type=None,
  fields=[
    _descriptor.FieldDescriptor(
      name='fvalue', full_name='dti.MNumber32.fvalue', index=0,
      number=1, type=11, cpp_type=10, label=1,
      has_default_value=False, default_value=None,
      message_type=None, enum_type=None, containing_type=None,
      is_extension=False, extension_scope=None,
      serialized_options=None, file=DESCRIPTOR),
    _descriptor.FieldDescriptor(
      name='uvalue', full_name='dti.MNumber32.uvalue', index=1,
      number=2, type=11, cpp_type=10, label=1,
      has_default_value=False, default_value=None,
      message_type=None, enum_type=None, containing_type=None,
      is_extension=False, extension_scope=None,
      serialized_options=None, file=DESCRIPTOR),
    _descriptor.FieldDescriptor(
      name='ivalue', full_name='dti.MNumber32.ivalue', index=2,
      number=3, type=11, cpp_type=10, label=1,
      has_default_value=False, default_value=None,
      message_type=None, enum_type=None, containing_type=None,
      is_extension=False, extension_scope=None,
      serialized_options=None, file=DESCRIPTOR),
  ],
  extensions=[
  ],
  nested_types=[],
  enum_types=[
  ],
  serialized_options=None,
  is_extendable=False,
  syntax='proto3',
  extension_ranges=[],
  oneofs=[
    _descriptor.OneofDescriptor(
      name='number', full_name='dti.MNumber32.number',
      index=0, containing_type=None, fields=[]),
  ],
  serialized_start=218,
  serialized_end=326,
)


_MNUMBER64 = _descriptor.Descriptor(
  name='MNumber64',
  full_name='dti.MNumber64',
  filename=None,
  file=DESCRIPTOR,
  containing_type=None,
  fields=[
    _descriptor.FieldDescriptor(
      name='fvalue', full_name='dti.MNumber64.fvalue', index=0,
      number=1, type=11, cpp_type=10, label=1,
      has_default_value=False, default_value=None,
      message_type=None, enum_type=None, containing_type=None,
      is_extension=False, extension_scope=None,
      serialized_options=None, file=DESCRIPTOR),
    _descriptor.FieldDescriptor(
      name='uvalue', full_name='dti.MNumber64.uvalue', index=1,
      number=2, type=11, cpp_type=10, label=1,
      has_default_value=False, default_value=None,
      message_type=None, enum_type=None, containing_type=None,
      is_extension=False, extension_scope=None,
      serialized_options=None, file=DESCRIPTOR),
    _descriptor.FieldDescriptor(
      name='ivalue', full_name='dti.MNumber64.ivalue', index=2,
      number=3, type=11, cpp_type=10, label=1,
      has_default_value=False, default_value=None,
      message_type=None, enum_type=None, containing_type=None,
      is_extension=False, extension_scope=None,
      serialized_options=None, file=DESCRIPTOR),
  ],
  extensions=[
  ],
  nested_types=[],
  enum_types=[
  ],
  serialized_options=None,
  is_extendable=False,
  syntax='proto3',
  extension_ranges=[],
  oneofs=[
    _descriptor.OneofDescriptor(
      name='number', full_name='dti.MNumber64.number',
      index=0, containing_type=None, fields=[]),
  ],
  serialized_start=328,
  serialized_end=436,
)

_MNUMBER32.fields_by_name['fvalue'].message_type = _MF32
_MNUMBER32.fields_by_name['uvalue'].message_type = _MU32
_MNUMBER32.fields_by_name['ivalue'].message_type = _MI32
_MNUMBER32.oneofs_by_name['number'].fields.append(
  _MNUMBER32.fields_by_name['fvalue'])
_MNUMBER32.fields_by_name['fvalue'].containing_oneof = _MNUMBER32.oneofs_by_name['number']
_MNUMBER32.oneofs_by_name['number'].fields.append(
  _MNUMBER32.fields_by_name['uvalue'])
_MNUMBER32.fields_by_name['uvalue'].containing_oneof = _MNUMBER32.oneofs_by_name['number']
_MNUMBER32.oneofs_by_name['number'].fields.append(
  _MNUMBER32.fields_by_name['ivalue'])
_MNUMBER32.fields_by_name['ivalue'].containing_oneof = _MNUMBER32.oneofs_by_name['number']
_MNUMBER64.fields_by_name['fvalue'].message_type = _MF64
_MNUMBER64.fields_by_name['uvalue'].message_type = _MU64
_MNUMBER64.fields_by_name['ivalue'].message_type = _MI64
_MNUMBER64.oneofs_by_name['number'].fields.append(
  _MNUMBER64.fields_by_name['fvalue'])
_MNUMBER64.fields_by_name['fvalue'].containing_oneof = _MNUMBER64.oneofs_by_name['number']
_MNUMBER64.oneofs_by_name['number'].fields.append(
  _MNUMBER64.fields_by_name['uvalue'])
_MNUMBER64.fields_by_name['uvalue'].containing_oneof = _MNUMBER64.oneofs_by_name['number']
_MNUMBER64.oneofs_by_name['number'].fields.append(
  _MNUMBER64.fields_by_name['ivalue'])
_MNUMBER64.fields_by_name['ivalue'].containing_oneof = _MNUMBER64.oneofs_by_name['number']
DESCRIPTOR.message_types_by_name['MString'] = _MSTRING
DESCRIPTOR.message_types_by_name['MU32'] = _MU32
DESCRIPTOR.message_types_by_name['MU64'] = _MU64
DESCRIPTOR.message_types_by_name['MI32'] = _MI32
DESCRIPTOR.message_types_by_name['MI64'] = _MI64
DESCRIPTOR.message_types_by_name['MF32'] = _MF32
DESCRIPTOR.message_types_by_name['MF64'] = _MF64
DESCRIPTOR.message_types_by_name['MBytes'] = _MBYTES
DESCRIPTOR.message_types_by_name['MNumber32'] = _MNUMBER32
DESCRIPTOR.message_types_by_name['MNumber64'] = _MNUMBER64
_sym_db.RegisterFileDescriptor(DESCRIPTOR)

MString = _reflection.GeneratedProtocolMessageType('MString', (_message.Message,), dict(
  DESCRIPTOR = _MSTRING,
  __module__ = 'protobuf.utils_pb2'
  # @@protoc_insertion_point(class_scope:dti.MString)
  ))
_sym_db.RegisterMessage(MString)

MU32 = _reflection.GeneratedProtocolMessageType('MU32', (_message.Message,), dict(
  DESCRIPTOR = _MU32,
  __module__ = 'protobuf.utils_pb2'
  # @@protoc_insertion_point(class_scope:dti.MU32)
  ))
_sym_db.RegisterMessage(MU32)

MU64 = _reflection.GeneratedProtocolMessageType('MU64', (_message.Message,), dict(
  DESCRIPTOR = _MU64,
  __module__ = 'protobuf.utils_pb2'
  # @@protoc_insertion_point(class_scope:dti.MU64)
  ))
_sym_db.RegisterMessage(MU64)

MI32 = _reflection.GeneratedProtocolMessageType('MI32', (_message.Message,), dict(
  DESCRIPTOR = _MI32,
  __module__ = 'protobuf.utils_pb2'
  # @@protoc_insertion_point(class_scope:dti.MI32)
  ))
_sym_db.RegisterMessage(MI32)

MI64 = _reflection.GeneratedProtocolMessageType('MI64', (_message.Message,), dict(
  DESCRIPTOR = _MI64,
  __module__ = 'protobuf.utils_pb2'
  # @@protoc_insertion_point(class_scope:dti.MI64)
  ))
_sym_db.RegisterMessage(MI64)

MF32 = _reflection.GeneratedProtocolMessageType('MF32', (_message.Message,), dict(
  DESCRIPTOR = _MF32,
  __module__ = 'protobuf.utils_pb2'
  # @@protoc_insertion_point(class_scope:dti.MF32)
  ))
_sym_db.RegisterMessage(MF32)

MF64 = _reflection.GeneratedProtocolMessageType('MF64', (_message.Message,), dict(
  DESCRIPTOR = _MF64,
  __module__ = 'protobuf.utils_pb2'
  # @@protoc_insertion_point(class_scope:dti.MF64)
  ))
_sym_db.RegisterMessage(MF64)

MBytes = _reflection.GeneratedProtocolMessageType('MBytes', (_message.Message,), dict(
  DESCRIPTOR = _MBYTES,
  __module__ = 'protobuf.utils_pb2'
  # @@protoc_insertion_point(class_scope:dti.MBytes)
  ))
_sym_db.RegisterMessage(MBytes)

MNumber32 = _reflection.GeneratedProtocolMessageType('MNumber32', (_message.Message,), dict(
  DESCRIPTOR = _MNUMBER32,
  __module__ = 'protobuf.utils_pb2'
  # @@protoc_insertion_point(class_scope:dti.MNumber32)
  ))
_sym_db.RegisterMessage(MNumber32)

MNumber64 = _reflection.GeneratedProtocolMessageType('MNumber64', (_message.Message,), dict(
  DESCRIPTOR = _MNUMBER64,
  __module__ = 'protobuf.utils_pb2'
  # @@protoc_insertion_point(class_scope:dti.MNumber64)
  ))
_sym_db.RegisterMessage(MNumber64)


DESCRIPTOR._options = None
# @@protoc_insertion_point(module_scope)
