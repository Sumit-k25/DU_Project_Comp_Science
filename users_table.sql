create table if not exists public.users (
  id bigint generated always as identity primary key,
  tic_email text not null unique,
  password text not null,
  name text,
  created_at timestamp with time zone default now()
);

-- Example row (replace with your real TIC credentials)
insert into public.users (tic_email, password, name)
values ('tic@example.com', '123456', 'TIC Admin')
on conflict (tic_email) do nothing;
