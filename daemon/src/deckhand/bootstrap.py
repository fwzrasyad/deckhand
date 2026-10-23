"""Composition root: builds the object graph and starts services in order.

Layer 4 (edge). This is the only place where concrete implementations are wired
to interfaces; every other module receives its collaborators through
``typing.Protocol`` interfaces.
"""
