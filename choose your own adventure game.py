name = input("Type your name: ")
print("Welcome",name,"to this adventure！")

answer = input(
      "You are on a dirt road,it has come to an end and you can go left or right.which way would you like to go? ").lower()

if answer == "left":
    answer = input("You come to a river,you can walk around it or swim across? Type walk to walk and swim to swim across: ")

    if answer=="swim":
        print("You swam across and were eaten by an alligator.")
    elif answer=="walk":
        print("You walked for many miles, ran out of water and you lost the game.")
    else:
        print("Not a valid option. You lose")

elif answer=="right":
    answer = input("You come to a bridge,it looks wobbly,do you want to cross it or head back (cross/back) ")
    if answer =="cross":
        answer=input("You cross the bridge and meet a stranger.Do you talk to them (yes/no)?")
        if answer == "yes":
            print("You talk to the strange and they give you gold.You WIN!")
        elif answer =="no":
            print("You ignore the stranger and they are offended and you lose.")
        else:
            print("Not a valid option. You lose.")
    elif answer =="back":
        print("You go back and lose.")
else:
    print("Not a valid option. You lose.")

print("Thank you for trying",name)