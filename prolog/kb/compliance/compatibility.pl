%% License compatibility and risk between project and dependency licenses.

%% Same license is always compatible.
compatible(P, D) :- P = D.

%% Permissive projects may use permissive dependencies.
compatible(P, D) :-
    license_family(P, permissive),
    license_family(D, permissive).

%% Weak copyleft dependency in permissive project: generally OK if dynamically linked
%% (simplified: allowed with medium risk handled separately).
compatible(P, D) :-
    license_family(P, permissive),
    license_family(D, weak_copyleft).

compatible(P, D) :-
    license_family(P, weak_copyleft),
    license_family(D, permissive).

compatible(P, D) :-
    license_family(P, weak_copyleft),
    license_family(D, weak_copyleft).

%% Strong copyleft project with permissive deps: OK when combined work stays under GPL.
compatible(P, D) :-
    license_family(P, strong_copyleft),
    license_family(D, permissive).

compatible(P, D) :-
    license_family(P, strong_copyleft),
    license_family(D, weak_copyleft).

compatible(P, D) :-
    license_family(P, strong_copyleft),
    license_family(D, strong_copyleft),
    P = D.

%% Incompatibilities
incompatible(P, D, strong_copyleft_in_permissive_project) :-
    license_family(P, permissive),
    license_family(D, strong_copyleft).

incompatible(P, D, permissive_in_strong_copyleft_violation) :-
    license_family(P, strong_copyleft),
    license_family(D, permissive),
    P \= gpl_2_0,
    P \= gpl_3_0.

incompatible(P, D, agpl_network_obligation_conflict) :-
    license_family(P, permissive),
    D = agpl_3_0.

incompatible(P, D, agpl_network_obligation_conflict) :-
    license_family(P, weak_copyleft),
    D = agpl_3_0,
    P \= agpl_3_0.

incompatible(P, D, proprietary_dependency_blocked) :-
    P \= proprietary,
    D = proprietary.

incompatible(P, D, unknown_dependency_requires_review) :-
    D = unknown,
    P \= unknown.

incompatible(P, D, proprietary_project_blocks_copyleft) :-
    P = proprietary,
    is_copyleft(D).

%% Risk levels (project P incorporating dependency D)
risk_level(_, D, critical) :- D = unknown.
risk_level(P, D, critical) :- incompatible(P, D, _).

risk_level(P, D, high) :-
    \+ incompatible(P, D, _),
    license_family(P, permissive),
    license_family(D, strong_copyleft).

risk_level(P, D, high) :-
    \+ incompatible(P, D, _),
    P = agpl_3_0,
    license_family(D, permissive).

risk_level(P, D, medium) :-
    \+ incompatible(P, D, _),
    \+ risk_level(P, D, high),
    \+ risk_level(P, D, critical),
    license_family(D, weak_copyleft),
    license_family(P, permissive).

risk_level(P, D, medium) :-
    \+ incompatible(P, D, _),
    requires_source_disclosure(D),
    license_family(P, permissive).

risk_level(P, D, low) :-
    compatible(P, D),
    \+ risk_level(P, D, critical),
    \+ risk_level(P, D, high),
    \+ risk_level(P, D, medium).

risk_level(P, D, medium) :-
    \+ compatible(P, D),
    \+ incompatible(P, D, _),
    \+ risk_level(P, D, critical),
    \+ risk_level(P, D, high).
