"""Quarantined network sub-package.

``publishing_house.net.fetch`` is the SOLE sanctioned network-access module in the
codebase (rule 18 carve-out). It performs GET-only, host-allowlisted, cached
retrieval for category research. No other module in ``publishing_house`` may import
a network library. ``fetch`` itself MUST NOT import state/gate/generator/verifier
modules — it depends only on the standard library.
"""
