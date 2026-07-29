create table if not exists public.users (
  id bigint generated always as identity primary key,
  tic_email text not null unique,
  password text not null,
  created_at timestamp with time zone default now(),
  constraint users_tic_email_fkey foreign key (tic_email)
    references public.Teachers_Data (Mail)
    on delete cascade
);

insert into public.users (tic_email, password)
values ('tic@example.com', '123456')
on conflict (tic_email) do nothing;
