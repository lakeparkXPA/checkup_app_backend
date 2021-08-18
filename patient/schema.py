import graphene
from graphene_django.types import DjangoObjectType


from patient.models import PInfo, PLogin


class PLoginType(DjangoObjectType):
    class Meta:
        model = PLogin
        fields = ('p_id', 'email', 'password', 'agreed')



class PInfoType(DjangoObjectType):
    class Meta:
        model = PInfo
        fields = ('p_info_id', 'p', 'name', 'birth', 'sex')


class Query(graphene.ObjectType):
    plogin = graphene.List(PLoginType)
    pinfo = graphene.List(PInfoType)

    def resolve_plogin(root, info, **kwargs):
        return PLogin.objects.all()

    def resolve_pinfo(root, info, **kwargs):
        return PInfo.objects.all()


class PloginInput(graphene.InputObjectType):
    email = graphene.String(required=True)
    password = graphene.String(required=True)
    agreed = graphene.Boolean()


class CreatePLogin(graphene.Mutation):
    class Arguments:
        input = PloginInput()

    plogin = graphene.Field(PLoginType)


    @classmethod
    def mutate(cls, root, info, input):
        plogin = PLogin()
        plogin.email = input.email
        plogin.password = input.password
        plogin.agreed = input.agreed
        plogin.save()
        return CreatePLogin(plogin=plogin)

class UpdatePlogin(graphene.Mutation):
    class Arguments:
        input = PloginInput()
        id = graphene.ID()

    plogin = graphene.Field(PLoginType)

    @classmethod
    def mutate(cls, root, info, input, id):
        plogin = PLogin.objects.get(p_id=id)
        plogin.email = input.email
        plogin.password = input.password
        plogin.agreed = input.agreed
        plogin.save()
        return UpdatePlogin(plogin=plogin)


class PInfoInput(graphene.InputObjectType):
    email = graphene.String(required=True)
    password = graphene.String(required=True)
    agreed = graphene.Boolean()

    name = graphene.String()
    birth = graphene.Date()
    sex = graphene.Int()


class CreatePInfo(graphene.Mutation):
    class Arguments:
        input = PInfoInput()

    pinfo = graphene.Field(PInfoType)

    @classmethod
    def mutate(cls, root, info, input):
        plogin = PLogin()
        plogin.email = input.email
        plogin.password = input.password
        plogin.agreed = input.agreed
        plogin.save()

        p_fk = plogin
        pinfo = PInfo()
        pinfo.p = p_fk
        pinfo.name = input.name
        pinfo.birth = input.birth
        pinfo.sex = input.sex
        pinfo.save()
        return CreatePInfo(pinfo=pinfo)



class UpdatePInfo(graphene.Mutation):
    class Arguments:
        input = PInfoInput()
        id = graphene.ID()

    pinfo = graphene.Field(PInfoType)

    @classmethod
    def mutate(cls, root, info, input, id):
        pinfo = PInfo(p_info_id=id)
        pinfo.name = input.name
        pinfo.birth = input.birth
        pinfo.sex = input.sex
        pinfo.save()

        p_fk = pinfo
        plogin = PLogin.objects.get(p_id=p_fk)
        plogin.email = input.email
        plogin.password = input.password
        plogin.agreed = input.agreed
        plogin.save()

        return UpdatePInfo(pinfo=pinfo)

class Mutation(graphene.ObjectType):
    create_plogin = CreatePLogin.Field()
    update_plogin = UpdatePlogin.Field()
    create_pinfo = CreatePInfo.Field()
    update_pinfo = UpdatePInfo.Field()


schema = graphene.Schema(query=Query, mutation=Mutation)