# -*- coding: utf-8 -*-

import functools
from abc import ABCMeta

from params import StaticParam

# exempt from metaclass business
ABSTRACT_BASES = ['Operation', 'QueryOperation']


def get_inputless_init(old_init):
    """
    Used for Operations like get_random() which don't take an input
    parameter.
    """
    if getattr(old_init, '_is_inputless', None):
        return old_init

    @functools.wraps(old_init)
    def inputless_init(self, limit=None, **kw):
        kw['input_param'] = None
        return old_init(self, limit=limit, **kw)
    inputless_init._is_inputless = True
    return inputless_init


class OperationMeta(ABCMeta):
    _all_ops = []

    def __new__(cls, name, bases, attrs):
        ret = super(OperationMeta, cls).__new__(cls, name, bases, attrs)
        if name in ABSTRACT_BASES:
            return ret
        subop_chain = getattr(ret, 'subop_chain', [])
        try:
            input_field = ret.input_field
        except AttributeError:
            input_field = subop_chain[0].input_field
            ret.input_field = input_field
        if input_field is None:
            ret.__init__ = get_inputless_init(ret.__init__)
        else:
            input_field.required = True
        # TODO: run through subop_chain, checking the outputs match up
        try:
            output_type = ret.output_type
        except AttributeError:
            output_type = subop_chain[-1].singular_output_type
            for st in subop_chain:
                if not st.is_bijective:
                    output_type = [output_type]
                    break
            ret.output_type = output_type

        try:
            ret.singular_output_type = ret.output_type[0]
        except (TypeError, IndexError):
            ret.singular_output_type = ret.output_type

        # TODO: support manual overrides for the following?
        ret.is_multiargument = getattr(input_field, 'multi', False)
        ret.is_bijective = True
        if type(output_type) is list and output_type:
            ret.is_bijective = False

        for ex in getattr(ret, 'examples', []):
            ex.bind_op_type(ret)

        ret.__doc__ = (ret.__doc__ and ret.__doc__ + '\n') or ''
        ret.__doc__ += operation_signature_doc(ret)
        cls._all_ops.append(ret)
        return ret

    @property
    def help_str(self):
        ret = '\n\t'.join([self.__name__] + self.__doc__.strip().split('\n'))

        # TODO move options and examples to the __doc__

        ret += '\n'
        return ret


"""
class OperationMeta(type):
    def __new__(cls, name, bases, attrs):
        ret = super(OperationMeta, cls).__new__(cls, name, bases, attrs)
        if name in ABSTRACT_BASES:
            return ret
        input_field = ret.input_field
        if input_field is None:
            ret.__init__ = get_inputless_init(ret.__init__)
        else:
            input_field.required = True
        output_type = ret.output_type
        try:
            ret.singular_output_type = output_type[0]
        except (TypeError, IndexError):
            ret.singular_output_type = output_type

        ret.is_multiargument = getattr(input_field, 'multi', False)
        ret.is_bijective = True
        if type(output_type) is list and output_type:
            ret.is_bijective = False

        for ex in getattr(ret, 'examples', []):
            ex.bind_op_type(ret)

        ret.__doc__ = (ret.__doc__ and ret.__doc__ + '\n') or ''
        ret.__doc__ += operation_signature_doc(ret)
        cls._all_ops.append(ret)
        return ret


class CompoundOperationMeta(OperationMeta):
    def __new__(cls, name, bases, attrs):
        subop_chain =
        ret = super(CompoundOperationMeta, cls).__new__(cls, name, bases, attrs)
        if name == 'Operation' or name == 'QueryOperation':
            return ret  # TODO: add elegance?
        subop_chain = getattr(ret, 'subop_chain', [])
        try:
            input_field = ret.input_field
        except AttributeError:
            input_field = subop_chain[0].input_field
            ret.input_field = input_field
        if input_field is None:
            ret.__init__ = get_inputless_init(ret.__init__)
        else:
            input_field.required = True
        # TODO: run through subop_chain, checking the outputs match up
        try:
            output_type = ret.output_type
        except AttributeError:
            output_type = subop_chain[-1].singular_output_type
            for st in subop_chain:
                if not st.is_bijective:
                    output_type = [output_type]
                    break
            ret.output_type = output_type

        try:
            ret.singular_output_type = ret.output_type[0]
        except (TypeError, IndexError):
            ret.singular_output_type = ret.output_type

        # TODO: support manual overrides for the following?
        ret.is_multiargument = getattr(input_field, 'multi', False)
        ret.is_bijective = True
        if type(output_type) is list and output_type:
            ret.is_bijective = False

        for ex in getattr(ret, 'examples', []):
            ex.bind_op_type(ret)

        ret.__doc__ = (ret.__doc__ and ret.__doc__ + '\n') or ''
        ret.__doc__ += operation_signature_doc(ret)
        cls._all_ops.append(ret)
        return ret
"""


def get_field_str(field):
    out_str = field.key
    mods = []
    if field.required:
        mods.append('required')
    if field.multi:
        mods.append('multi')
    if mods:
        out_str += ' (%s)' % ', '.join(mods)
    return out_str


def operation_signature_doc(operation):
    if operation.input_field is None:
        doc_input = 'None'
    else:
        doc_input = operation.input_field.key
    doc_output = operation.singular_output_type.__name__
    doc_template = 'Input: %s\n'
    if operation.is_bijective:
        doc_template += 'Output: %s\n'
    else:
        doc_template += 'Output: List of %s\n'

    print_fields = [f for f in getattr(operation, 'fields', [])
                    if not isinstance(f, StaticParam)]
    if print_fields:
        doc_template += 'Options: '
        doc_template += ','.join([get_field_str(f) for f in print_fields]) + '\n'

    if hasattr(operation, 'examples'):
        doc_template += 'Examples: \n\t'
        doc_template += '\n\t'.join([repr(x) for x in operation.examples]) + '\n'

    return doc_template % (doc_input, doc_output)
