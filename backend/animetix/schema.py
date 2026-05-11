import graphene
from graphene_django import DjangoObjectType
from .models import Profile, DailyChallenge, Achievement
from .services import AnimetixService

animetix_service = AnimetixService()

class ProfileType(DjangoObjectType):
    class Meta:
        model = Profile
        fields = "__all__"

class DailyChallengeType(DjangoObjectType):
    class Meta:
        model = DailyChallenge
        fields = "__all__"

class MediaItemType(graphene.ObjectType):
    id = graphene.String()
    title = graphene.String()
    title_english = graphene.String()
    image = graphene.String()
    year = graphene.Int()
    popularity = graphene.Int()
    genres = graphene.List(graphene.String)
    tags = graphene.List(graphene.String)
    micro_tags = graphene.List(graphene.String)
    description = graphene.String()
    
    # Nœuds du Graphe de Connaissances
    studios = graphene.List(graphene.String)
    author = graphene.String()
    related_items = graphene.List(lambda: MediaItemType)

    def resolve_studios(self, info):
        return self.get('graph_nodes', {}).get('studios', [])

    def resolve_author(self, info):
        return self.get('graph_nodes', {}).get('author')

class Query(graphene.ObjectType):
    me = graphene.Field(ProfileType)
    daily_challenge = graphene.Field(DailyChallengeType)
    search_media = graphene.List(MediaItemType, q=graphene.String(), media_type=graphene.String())
    media_details = graphene.Field(MediaItemType, id=graphene.String(), media_type=graphene.String())

    def resolve_me(self, info):
        if info.context.user.is_authenticated:
            return info.context.user.profile
        return None

    def resolve_daily_challenge(self, info):
        import datetime
        return DailyChallenge.objects.filter(date=datetime.date.today()).first()

    def resolve_search_media(self, info, q, media_type="Anime"):
        data = animetix_service.load_data(media_type)
        if not data: return []
        return [item for item in data['lookup'] if q.lower() in item['title'].lower()][:10]

    def resolve_media_details(self, info, id, media_type="Anime"):
        data = animetix_service.load_data(media_type)
        if not data: return None
        # Recherche par ID dans la DB propre
        for item in data['db']:
            if str(item['id']) == str(id):
                return item
        return None

schema = graphene.Schema(query=Query)
