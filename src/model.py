class Account(base):  # Аккаунты юзеров
    id = Column(Integer, primary_key=True)

    last_username_reset = Column(DateTime)

    registration_date = Column(DateTime)

    # Права пользователей
    admin = Column(
        Boolean, default=False
    )  # только админ может менять грейды у всех юзеров, а так же назначать новых админов и назначать права юзерам, дает доступ ко всем правам

    write_comments = Column(Boolean, default=True)  # писать и редактировать
    set_reactions = Column(Boolean, default=True)

    create_reactions = Column(Boolean, default=False)

    mute_until = Column(
        DateTime
    )  # временное ограничение на все права социальными действиями на сервисе, активен если время тут больше текущего
    mute_users = Column(Boolean, default=False)  # право на мут пользователей

    publish_mods = Column(Boolean, default=True)
    change_authorship_mods = Column(Boolean, default=False)
    change_self_mods = Column(Boolean, default=True)
    change_mods = Column(Boolean, default=False)
    delete_self_mods = Column(Boolean, default=True)
    delete_mods = Column(Boolean, default=False)

    create_forums = Column(Boolean, default=True)
    change_authorship_forums = Column(Boolean, default=False)
    change_self_forums = Column(Boolean, default=True)
    change_forums = Column(Boolean, default=False)
    delete_self_forums = Column(Boolean, default=True)
    delete_forums = Column(Boolean, default=False)

    change_username = Column(Boolean, default=True)
    last_username_reset = Column(DateTime)
    change_about = Column(Boolean, default=True)
    change_avatar = Column(Boolean, default=True)

    vote_for_reputation = Column(Boolean, default=True)