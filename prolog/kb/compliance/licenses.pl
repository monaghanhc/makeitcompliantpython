%% Canonical license identifiers for rule-based compliance reasoning.
%% Atoms are stable API keys; display names are resolved in Python.

license(mit).
license(apache_2_0).
license(bsd_2_clause).
license(bsd_3_clause).
license(gpl_2_0).
license(gpl_3_0).
license(lgpl_2_1).
license(lgpl_3_0).
license(agpl_3_0).
license(mpl_2_0).
license(eclipse_2_0).
license(unlicense).
license(isc).
license(postgresql).
license(zlib).
license(proprietary).
license(unknown).

%% SPDX-style aliases (normalized by Python before assert)
license_alias('MIT', mit).
license_alias('Apache-2.0', apache_2_0).
license_alias('BSD-2-Clause', bsd_2_clause).
license_alias('BSD-3-Clause', bsd_3_clause).
license_alias('GPL-2.0-only', gpl_2_0).
license_alias('GPL-3.0-only', gpl_3_0).
license_alias('LGPL-2.1-only', lgpl_2_1).
license_alias('LGPL-3.0-only', lgpl_3_0).
license_alias('AGPL-3.0-only', agpl_3_0).
license_alias('MPL-2.0', mpl_2_0).
license_alias('EPL-2.0', eclipse_2_0).
license_alias('Unlicense', unlicense).
license_alias('ISC', isc).
license_alias('PostgreSQL', postgresql).
license_alias('Zlib', zlib).

resolve_license(Id, Id) :- license(Id).
resolve_license(Alias, Id) :- license_alias(Alias, Id).
