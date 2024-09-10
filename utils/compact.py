from dataclasses import fields


class Compact:

    def __repr__(self) -> None:
        """Just a fancy multiline repr"""
        cls = self.__class__
        cls_name = cls.__name__
        indent = ' ' * 4
        res = [f'{cls_name}(']
        for f in fields(cls):
            value = getattr(self, f.name)
            res.append(f'{indent}{f.name} = {value!r},')

        res.append(')')
        return '\n'.join(res)
