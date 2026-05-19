:- begin_tests(compliance_rules).

:- consult(licenses).
:- consult(families).
:- consult(obligations).
:- consult(requirements).
:- consult(compatibility).
:- consult(analysis).

test(mit_is_permissive) :-
    license_family(mit, permissive).

test(mit_apache_compatible) :-
    compatible(mit, apache_2_0).

test(mit_gpl3_incompatible) :-
    incompatible(mit, gpl_3_0, strong_copyleft_in_permissive_project).

test(analyze_dependency_mit_gpl3) :-
    analyze_dependency(mit, gpl_3_0, result(no, Risk, Conflicts)),
    member(strong_copyleft_in_permissive_project, Conflicts),
    member(Risk, [high, critical]).

test(required_obligations_mit) :-
    required_obligations(mit, [apache_2_0], Obligations),
    member(include_copyright_notice, Obligations).

test(explain_incompatibility_nonempty) :-
    explain_incompatibility(mit, gpl_3_0, Explanation),
    string(Explanation),
    Explanation \= ''.

:- end_tests(compliance_rules).
