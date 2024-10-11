from django.core.exceptions import ValidationError
from django.db import models

from modelcluster.fields import ParentalKey
from modelcluster.contrib.taggit import ClusterTaggableManager
from taggit.models import TaggedItemBase

from wagtail.models import Page
from wagtail.fields import RichTextField, StreamField
from wagtail.admin.panels import FieldPanel
from wagtail import blocks
from wagtail.documents.blocks import DocumentChooserBlock
from wagtail.snippets.blocks import SnippetChooserBlock
from wagtail.models import TranslatableMixin, BootstrapTranslatableMixin

from blocks import blocks as custom_blocks

from django.contrib.contenttypes.fields import GenericRelation
from wagtail.admin.panels import PublishingPanel
from wagtail.models import DraftStateMixin, RevisionMixin, LockableMixin, PreviewableMixin

from wagtail.search import index
from wagtail.api import APIField
from wagtail.images import get_image_model
from rest_framework.fields import Field

from wagtail.contrib.routable_page.models import RoutablePageMixin, path, re_path
from django.http import JsonResponse
from wagtail.templatetags.wagtailcore_tags import richtext

from django.core.paginator import EmptyPage, PageNotAnInteger, Paginator
from wagtail.embeds.blocks import EmbedBlock

from wagtailcharts.blocks import ChartBlock

class BlogIndex(RoutablePageMixin, Page):
    blog_page = models.ForeignKey('wagtailcore.Page',
                                  on_delete=models.PROTECT,
                                    related_name='+'
                                  )
    



    template = 'blogpages/blog_index_page.html'
    max_count = 1
    parent_page_types = ['home.HomePage']
    subpage_types = ['blogpages.BlogDetail']

    subtitle = models.CharField(max_length=100, blank=True)
    body = RichTextField(blank=True)

    content_panels = Page.content_panels + [
        FieldPanel('subtitle'),
        FieldPanel('body'),
    ]

    # Example path that overwrites the default blog index page.
    # This is currently more work that using `get_context()` in the BlogIndex class.
    # @path('')
    # def default_blog_page(self, request):
    #     course_name = "The Ultimate Wagtail Developers Course"

    #     return self.render(
    #         request,
    #         context_overrides={
    #             'course_name': course_name
    #         }
    #     )

    def get_sitemap_urls(self, request=None):
        sitemap = super().get_sitemap_urls(request)
        last_mod = BlogDetail.objects.live().order_by('-last_published_at').first()
        sitemap.append({
            'location': self.get_full_url(request) + self.reverse_subpage("all"),
            'lastmod': (last_mod.last_published_at or last_mod.latest_revision_created_at),
        })
        sitemap.append({
            'location': self.get_full_url(request) + self.reverse_subpage("tag", args=["wagtail"]),
        })
        sitemap.append({
            'location': self.get_full_url(request) + self.reverse_subpage("tags", args=[2024]),
        })
        return sitemap


    # /blog/all/ is what this will generate.
    @path('all/', name='all')
    def all_blog_posts(self, request):
        posts = BlogDetail.objects.live().public()

        return self.render(
            request,
            context_overrides={
                'posts': posts
            }
        )

    # /blog/tag/{tagName}/
    # /blog/tags/{tagName}/
    @path('tag/<str:tag>/', name='tag')
    @path('tags/<str:tag>/', name='tags')
    def blog_posts_by_tag(self, request, tag=None):
        posts = BlogDetail.objects.live().public().filter(tags__name=tag)

        if not tag:
            ... # redirect in here

        return self.render(
            request,
            context_overrides={
                'posts': posts,
                'tag': tag
            },
            template='blogpages/blog_tag_page.html'
        )

    # uses regular expression path (re_path) to match the year
    # /blog/api/2025/ as an example
    @re_path(r'^api/(\d+)/$', name='api')
    def api_response(self, request, year):
        posts = BlogDetail.objects.live().public().filter(first_published_at__year=year)
        return JsonResponse({
            'year': year,
            'posts': list(posts.values('title', 'first_published_at'))
        })

    #original
    # def get_context(self, request):
    #     context = super().get_context(request)
    #     context['blogpages'] = BlogDetail.objects.live().public()[:5]
    #     return context

    def get_context(self, request, *args, **kwargs):

        # Update context to include only published posts, ordered by reverse-chron
        context = super().get_context(request, *args, **kwargs)
        context['total_posts'] = BlogDetail.objects.live().count()
        blogpages = self.get_children().live().public().order_by('-first_published_at')[:5]
        context['blogpages'] = blogpages
                # Get all posts
        all_posts = BlogDetail.objects.live().public().order_by('-first_published_at')
        # Paginate all posts by 4 per page
        paginator = Paginator(all_posts, 4)
        # Try to get the ?page=x value
        page = request.GET.get("page")
        try:
            # If the page exists and the ?page=x is an int
            posts = paginator.page(page)
        except PageNotAnInteger:
            # If the ?page=x is not an int; show the first page
            posts = paginator.page(1)
        except EmptyPage:
            # If the ?page=x is out of range (too high most likely)
            # Then return the last page
            posts = paginator.page(paginator.num_pages)

        # "posts" will have child pages; you'll need to use .specific in the template
        # in order to access child properties, such as youtube_video_id and subtitle
        context["posts"] = posts
        return context

class BlogPageTags(TaggedItemBase):
    content_object = ParentalKey(
        'blogpages.BlogDetail',
        related_name='tagged_items',
        on_delete=models.CASCADE,
    )

class AuthorSerializer(Field):
    def to_representation(self, value):
        return {
            'name': value.name,
            'bio': value.bio,
        }

class ImageSerializer(Field):
    def to_representation(self, value):
        return {
            "original": {
                'url': value.file.url,
                'width': value.width,
                'height': value.height,
            },
            "thumbnail": {
                'url': value.get_rendition('max-165x165').url,
                'width': value.get_rendition('max-165x165').width,
                'height': value.get_rendition('max-165x165').height,
            },
            "small": {
                'url': value.get_rendition('max-300x300').url,
                'width': value.get_rendition('max-300x300').width,
                'height': value.get_rendition('max-300x300').height,
            },
            "medium": {
                'url': value.get_rendition('max-700x700').url,
                'width': value.get_rendition('max-700x700').width,
                'height': value.get_rendition('max-700x700').height,
            },
        }


class RichTextFieldSerializer(Field):
    def to_representation(self, value):
        return richtext(value)


class BlogDetail(Page):

    from wagtailmodelchooser.blocks import ModelChooserBlock

    def get_context(self, request):
        context = super().get_context(request)
        context['blog_index'] = BlogIndex.objects.first()
        return context
    
    def get_absolute_url(self):
        try:
            site_id, site_root_url, relative_page_path = self.get_url_parts()
            ret = relative_page_path
        except TypeError:
            ret = None
        return ret

    
    template = 'blogpages/blog_detail.html'
    # Below will overwrite the `PASSWORD_REQUIRED_TEMPLATE` setting in settings/base.py
    # password_required_template = 'blogpages/password_in_here_file.html'

    subtitle = models.CharField(max_length=100, blank=True)
    tags = ClusterTaggableManager(through=BlogPageTags, blank=True)
    author = models.ForeignKey(
        'blogpages.Author',
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name='+'
    )

    image = models.ForeignKey(
        get_image_model(),
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name='+'
    )

    intro = RichTextField(blank=True)

    body = RichTextField(blank=True, null=True)
    
    COLORS = (
        ('#fa0000', 'Red'),
        ('#00ff00', 'Green'),
        ('#0000ff', 'Blue'),
    )

    chart_block = ChartBlock(colors=COLORS)

    stream = StreamField(
        [
            # ('struct', blocks.StructBlock([
            ('info', custom_blocks.InfoBlock()),
            ('richtext_content', custom_blocks.CustomRichTextBlock()),
            ('faq', custom_blocks.FAQListBlock()),
            ('embed', EmbedBlock(max_width=800, max_height=400, required=False)),
            ('doc', DocumentChooserBlock(
                group="Standalone blocks",required=False
                 )
            ),
            ('page', custom_blocks.CustomPageChooserBlock(required=False)),
            ('chart_block', custom_blocks.ChartBlock(required=False )), #, template="blogpages/chart.html"
        # ],
        #   template = 'struct_block.html'),
        ],
        blank=True,
        null=True,
    )

    parent_page_types = ['blogpages.BlogIndex']
    subpage_types = []

    def custom_content(self):
        return 150 / 3

    content_panels = Page.content_panels + [
        FieldPanel('image'),
        FieldPanel('intro'),
        FieldPanel('author', permission='home.add_author'),
        FieldPanel('body'),
        FieldPanel('subtitle'),
        FieldPanel('tags'),
        FieldPanel('stream'),
    ]

    api_fields = [
        APIField('subtitle'),
        APIField('intro', serializer=RichTextFieldSerializer()),
        APIField('image', serializer=ImageSerializer()),
        APIField('author', serializer=AuthorSerializer()),
        APIField('body'),
        APIField('custom_content'),
        APIField('tags'),
    ]

    def clean(self):
        super().clean()

        errors = {}

        # if 'blog' in self.title.lower():
        #     errors['title'] = "Title cannot have the word 'Blog'"

        # if 'blog' in self.subtitle.lower():
        #     errors['subtitle'] = "Subtitle cannot have the word 'Blog'"

        # if 'blog' in self.slug.lower():
        #     errors['slug'] = "Slug cannot have the word 'Blog'"

        if errors:
            raise ValidationError(errors)


# Author model for SnippetChooserBlock and ForeignKey's to the Author model.
# Panels go in the SnipeptViewSet in wagtail_hooks.py
class Author(
        TranslatableMixin,
        PreviewableMixin,  # Allows previews
        LockableMixin,  # Makes the model lockable
        DraftStateMixin,  # Needed for Drafts
        RevisionMixin,  # Needed for Revisions
        index.Indexed,  # Makes this searchable; don't forget to run python manage.py update_index
        models.Model
    ):
    name = models.CharField(max_length=100)
    bio = models.TextField()
    revisions = GenericRelation("wagtailcore.Revision", related_query_name="author")

    panels = [
        FieldPanel("name", permission="blogpages.can_edit_author_name"),
        FieldPanel("bio"),
        PublishingPanel(),
    ]

    search_fields = [
        index.FilterField('name'),
        index.SearchField('name'),
        index.AutocompleteField('name'),
    ]

    def __str__(self):
        return self.name

    @property
    def preview_modes(self):
        return PreviewableMixin.DEFAULT_PREVIEW_MODES + [
            ("dark_mode", "Dark Mode")
        ]

    def get_preview_template(self, request, mode_name):
        # return "includes/author.html"  # Default for a single preview template
        templates = {
            "": "includes/author.html", # Default
            "dark_mode": "includes/author_dark_mode.html"
        }
        return templates.get(mode_name, templates[""])

    def get_preview_context(self, request, mode_name):
        context = super().get_preview_context(request, mode_name)
        context['warning'] = "This is a preview"
        return context

    class Meta(TranslatableMixin.Meta):
        permissions = [
            ("can_edit_author_name", "Can edit author name")
        ]
