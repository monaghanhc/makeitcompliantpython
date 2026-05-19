%% High-level compliance analysis API (license atoms, no session facts required).
%%
%% analyze_dependency(ProjectLicense, DependencyLicense, Result).
%% analyze_project(ProjectLicense, DependencyLicenses, Report).
%% explain_incompatibility(ProjectLicense, DependencyLicense, Explanation).
%% required_obligations(ProjectLicense, DependencyLicenses, Obligations).

%% ---------------------------------------------------------------------------
%% analyze_dependency/3
%% Result = result(Compatible, Risk, Conflicts)
%%   Compatible: yes | no
%%   Risk: low | medium | high | critical
%%   Conflicts: list of incompatibility reason atoms
%% ---------------------------------------------------------------------------

analyze_dependency(Project, Dependency, result(Compatible, Risk, Conflicts)) :-
    dependency_compat_status(Project, Dependency, Compatible),
    risk_level(Project, Dependency, Risk),
    findall(Reason, incompatible(Project, Dependency, Reason), Conflicts).

dependency_compat_status(Project, Dependency, yes) :-
    compatible(Project, Dependency).
dependency_compat_status(Project, Dependency, no) :-
    \+ compatible(Project, Dependency).

%% ---------------------------------------------------------------------------
%% explain_incompatibility/3
%% Explanation: human-readable text (list of characters in SWI)
%% ---------------------------------------------------------------------------

explain_incompatibility(Project, Dependency, Explanation) :-
    incompatible(Project, Dependency, Reason),
    !,
    incompatibility_explanation(Reason, Explanation).

explain_incompatibility(Project, Dependency, Explanation) :-
    compatible(Project, Dependency),
    \+ incompatible(Project, Dependency, _),
    Explanation = 'Licenses are compatible under the configured rule set.'.

explain_incompatibility(_Project, _Dependency, Explanation) :-
    Explanation = 'No specific incompatibility rule matched; manual legal review advised.'.

incompatibility_explanation(strong_copyleft_in_permissive_project, Explanation) :-
    Explanation = 'A strong copyleft dependency in a permissive-licensed project can impose reciprocal obligations on the combined work when distributed.'.

incompatibility_explanation(permissive_in_strong_copyleft_violation, Explanation) :-
    Explanation = 'Combining permissive-only terms with a GPL-family project license may fail copyleft requirements for the combined work.'.

incompatibility_explanation(agpl_network_obligation_conflict, Explanation) :-
    Explanation = 'An AGPL dependency can require offering corresponding source to users who interact with the software over a network.'.

incompatibility_explanation(proprietary_dependency_blocked, Explanation) :-
    Explanation = 'A proprietary dependency cannot be redistributed with an open-source project without explicit permission.'.

incompatibility_explanation(unknown_dependency_requires_review, Explanation) :-
    Explanation = 'The dependency license is unknown; identify and record the license before release.'.

incompatibility_explanation(proprietary_project_blocks_copyleft, Explanation) :-
    Explanation = 'Copyleft dependencies conflict with proprietary project licensing for combined distribution.'.

%% ---------------------------------------------------------------------------
%% required_obligations/3
%% Obligations: sorted list of unique obligation atoms (project + dependencies)
%% ---------------------------------------------------------------------------

required_obligations(Project, DependencyLicenses, Obligations) :-
    findall(Obl, obligation(Project, Obl), ProjectObl),
    findall(Obl, (member(Dep, DependencyLicenses), obligation(Dep, Obl)), DepObl),
    append(ProjectObl, DepObl, Combined),
    sort(Combined, Obligations).

%% ---------------------------------------------------------------------------
%% analyze_project/3
%% Report = report(Obligations, DependencyAnalyses, OverallRisk)
%%   DependencyAnalyses: list of dep_analysis(License, Result)
%% ---------------------------------------------------------------------------

analyze_project(Project, DependencyLicenses, report(Obligations, Analyses, OverallRisk)) :-
    required_obligations(Project, DependencyLicenses, Obligations),
    maplist(analyze_one_dependency(Project), DependencyLicenses, Analyses),
    overall_project_risk(Project, DependencyLicenses, OverallRisk).

analyze_one_dependency(Project, Dependency, dep_analysis(Dependency, Result)) :-
    analyze_dependency(Project, Dependency, Result).

overall_project_risk(_Project, [], low).
overall_project_risk(Project, Dependencies, OverallRisk) :-
    findall(Risk, (member(Dep, Dependencies), risk_level(Project, Dep, Risk)), Risks),
    worst_risk(Risks, OverallRisk).

worst_risk([Risk], Risk).
worst_risk([Risk|Rest], Worst) :-
    worst_risk(Rest, W0),
    max_risk(Risk, W0, Worst).

max_risk(R1, R2, R1) :-
    risk_rank(R1, N1),
    risk_rank(R2, N2),
    N1 >= N2.
max_risk(_R1, R2, R2).

risk_rank(low, 0).
risk_rank(medium, 1).
risk_rank(high, 2).
risk_rank(critical, 3).
