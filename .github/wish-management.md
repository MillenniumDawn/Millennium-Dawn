# Wish management

Every wish for Millennium Dawn is a GitHub issue. The council manages them on one Project
board, "Millennium Dawn Wishes". This page records the fields, the views, the monthly
check, and the commands used to build the board.

## Rules the board enforces (2.1)

- One rework before two new countries per developer.
- A tagteam is two assignees on one issue.
- Every claimed wish has a council mentor.
- Every assignee hears from the council at least once a quarter.

## Intake

Wishes come in through the issue forms under `.github/ISSUE_TEMPLATE/`:

| Form       | Issue type  | Labels from the form                                        |
| ---------- | ----------- | ----------------------------------------------------------- |
| Focus tree | Focus Trees | `type:new-country` or `type:rework`, and `region:*`         |
| Task       | Task        | `type:update`, `type:system`, or `type:gfx`, and `region:*` |

`wish-intake.yml` reads the Kind, Work type, and Region dropdowns, applies the matching
labels, and adds any issue with a `type:*` label to the board. Assignees stay empty until
the council claims the wish.

## Where each field lives

| Field          | Lives in            | Values                                                                                                             |
| -------------- | ------------------- | ------------------------------------------------------------------------------------------------------------------ |
| Type           | repo label          | `type:new-country`, `type:rework`, `type:update`, `type:system`, `type:gfx`                                        |
| Region         | repo label          | `region:africa`, `region:latin-america`, `region:east-asia`, `region:middle-east`, `region:europe`, `region:other` |
| Target         | milestone           | `2.1`, `3.0`, or none for backlog                                                                                  |
| Stage          | board `Status`      | Wish, Claimed, In progress, Review, Done                                                                           |
| Council mentor | board single select | GitHub handles of the council                                                                                      |
| Last check-in  | board date          | Set at the quarterly ping                                                                                          |
| Developers     | assignees           | One, or two for a tagteam                                                                                          |

Labels and milestones are visible in the plain issue list; the three board fields are only
the council's.

## Views

| View               | Layout | Filter or grouping                      | Question it answers                       |
| ------------------ | ------ | --------------------------------------- | ----------------------------------------- |
| Wish pool          | table  | `status:Wish no:assignee`               | What is waiting for triage?               |
| Per dev            | board  | group by Assignees, `-status:Done`      | Who has two countries open and no rework? |
| Region coverage    | board  | group by Region label, `-status:Done`   | Where are the gaps?                       |
| Per council member | board  | group by Council mentor, `-status:Done` | Who mentors too much or nothing?          |

## Monthly council check

1. Open Per dev. Any developer with two `type:new-country` and no `type:rework` gets no new
   country until a rework closes.
2. Open Per council member. Rebalance mentors so no one carries more than a handful.
3. Open Region coverage. Flag empty regions to the Discord.
4. Filter on `label:needs-check-in`. Ping each assignee, set Last check-in to today. The
   label clears itself on the next comment or commit. `check-in-reminder.yml` applies it
   after 90 days without activity and never closes anything.

## Building the board

The board is <https://github.com/orgs/MillenniumDawn/projects/7>. It was built with the
commands below; rerun them to rebuild it. Needs
`gh auth refresh -h github.com -s project,read:project` once.

```
gh project create --owner MillenniumDawn --title "Millennium Dawn Wishes"
gh project field-create 7 --owner MillenniumDawn --name "Council mentor" \
  --data-type SINGLE_SELECT \
  --single-select-options "AngriestBird,Blazer135,TemplarGeneral,MrP0tter,KianGhk1530"
gh project field-create 7 --owner MillenniumDawn --name "Last check-in" --data-type DATE
gh project field-list 7 --owner MillenniumDawn --format json \
  --jq '.fields[] | select(.name=="Status") | .id'
gh api graphql -f query='mutation { updateProjectV2Field(input: { fieldId: "<id>",
  singleSelectOptions: [ {name: "Wish", color: GRAY, description: ""},
  {name: "Claimed", color: BLUE, description: ""}, {name: "In progress", color: YELLOW, description: ""},
  {name: "Review", color: ORANGE, description: ""}, {name: "Done", color: GREEN, description: ""} ] })
  { projectV2Field { ... on ProjectV2SingleSelectField { name } } } }'
```

Views have no API; create the four views above in the UI. Adding a mentor is
Settings > Council mentor > add option. The `PROJECT_PAT` repository secret must be able
to write to the project.
