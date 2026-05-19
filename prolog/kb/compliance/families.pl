%% License family classification for compatibility reasoning.
%% Load after licenses.pl.

license_family(mit, permissive).
license_family(apache_2_0, permissive).
license_family(bsd_2_clause, permissive).
license_family(bsd_3_clause, permissive).
license_family(isc, permissive).
license_family(unlicense, permissive).
license_family(zlib, permissive).
license_family(postgresql, permissive).

license_family(lgpl_2_1, weak_copyleft).
license_family(lgpl_3_0, weak_copyleft).
license_family(mpl_2_0, weak_copyleft).
license_family(eclipse_2_0, weak_copyleft).

license_family(gpl_2_0, strong_copyleft).
license_family(gpl_3_0, strong_copyleft).
license_family(agpl_3_0, strong_copyleft).

license_family(proprietary, proprietary).
license_family(unknown, unknown).

is_permissive(L) :- license_family(L, permissive).
is_weak_copyleft(L) :- license_family(L, weak_copyleft).
is_strong_copyleft(L) :- license_family(L, strong_copyleft).
is_copyleft(L) :- is_weak_copyleft(L).
is_copyleft(L) :- is_strong_copyleft(L).
