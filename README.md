# aiotodoist
[todoist API](https://github.com/Doist/todoist-python) with async enabled using `aiohttp`.


# Changes
To enable asynchronous, there have plenty methods be changed to return `awaitable` instead, list below:

## API
  - `api._get`, `api_post` will be changed to return **coroutine**.
  - `api.sync`, `api.commit` will be changed to return **future**.

## Managers
All of those managers could be accessed via `api.<manager_name>`.

  - `activity.get`
  - `backups.get`
  - `business_users.invite`, `business_users.accept_invitation`, business_users.reject_invitation`
  - `completed.get_stats`, `completed.get_all`
  - `emails.get_or_create`, `emails.disable`
  - `items.get_completed`
  - `projects.get_archived`, `projects.get_data`
  - `quick.add`
  - `templates.import_into_project`, `templates.export_as_file`, `templates.exort_as_url`
  - `uploads.add`, `uploads.get`, `uploads.delete`
  - `user.delete`, `user.update_notification.setting`


Methods listed above, will return **coroutine**, and others will return **Future** :

  - `collaborator_states.sync`, `collaborators.sync`
  - `filters.sync`, `filters.get`
  - `invitations.sync`
  - `items.sync`
  - `labels.sync`
  - `live_notifications.sync`
  - `locations.sync`
  - `notes.sync`
  - `project_notes.sync`
  - `projects.sync`
  - `reminders.sync`
  - `sections.sync`
  - `user.sync`
