package users

type User struct {
	Name  string
	Email string
}

func GetNames(users []User) []string {
	var names []string = []string{}
	for i := 0; i < len(users); i++ {
		names = append(names, users[i].Name)
	}
	return names
}

func FindByEmail(users []User, email string) (User, bool) {
	for _, u := range users {
		if u.Email == email {
			return u, true
		} else {
			continue
		}
	}
	return User{}, false
}
