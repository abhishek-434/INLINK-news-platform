from django import forms
from .models import Article, Category, Tag


class ArticleForm(forms.ModelForm):
    tags_input = forms.CharField(
        required=False,
        label="Tags",
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'climate, artificial-intelligence, geopolitics (comma separated)'
        }),
        help_text="Separate tags with commas."
    )

    class Meta:
        model = Article
        fields = [
            'title',
            'subtitle',
            'category',
            'article_type',
            'excerpt',
            'content',
            'cover_image',
            'cover_caption',
            'cover_credit',
            'sources',
        ]
        widgets = {
            'title': forms.TextInput(attrs={
                'class': 'form-control form-control-lg',
                'placeholder': 'Enter a captivating, editorial headline...',
                'id': 'article-title-input'
            }),
            'subtitle': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Secondary deck or clarifying sub-headline...'
            }),
            'category': forms.Select(attrs={'class': 'form-select'}),
            'article_type': forms.Select(attrs={'class': 'form-select'}),
            'excerpt': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': 'Compelling summary or lede paragraph shown on discovery cards and to guests (150-300 characters)...'
            }),
            'content': forms.Textarea(attrs={
                'class': 'form-control font-monospace',
                'rows': 16,
                'id': 'article-content-editor',
                'placeholder': 'Write your complete story here. Standard HTML tags (<p>, <h3>, <blockquote>, <strong>, <em>, <ul>, <img>) are formatted and sanitized...'
            }),
            'cover_image': forms.FileInput(attrs={'class': 'form-control', 'id': 'cover-image-input'}),
            'cover_caption': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'e.g. A solitary researcher in Svalbard'}),
            'cover_credit': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'e.g. Photo by Maya Lin / INKLINE Archive'}),
            'sources': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': 'Primary citations, interviews, data repositories...'
            }),
        }

    def clean_title(self):
        title = self.cleaned_data.get('title', '').strip()
        if len(title) < 10:
            raise forms.ValidationError("Headline must be at least 10 characters long.")
        return title

    def clean_excerpt(self):
        excerpt = self.cleaned_data.get('excerpt', '').strip()
        if len(excerpt) < 30:
            raise forms.ValidationError("Summary/excerpt must be at least 30 characters long.")
        return excerpt

    def clean_content(self):
        content = self.cleaned_data.get('content', '').strip()
        if len(content) < 100:
            raise forms.ValidationError("Article content must be at least 100 characters long.")
        return content

    def save(self, commit=True):
        instance = super().save(commit=False)
        if commit:
            instance.save()
            # Process tags
            tags_str = self.cleaned_data.get('tags_input', '')
            if tags_str:
                tag_names = [t.strip().lower() for t in tags_str.split(',') if t.strip()]
                instance.tags.clear()
                for name in tag_names:
                    tag, _ = Tag.objects.get_or_create(name=name)
                    instance.tags.add(tag)
        return instance
