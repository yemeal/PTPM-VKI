from dishka import Provider, Scope, provide

from app.application.commands.comments.add.handler import AddCommentHandler
from app.application.commands.comments.delete.handler import (
    DeleteCommentHandler,
)
from app.application.commands.comments.update.handler import (
    UpdateCommentHandler,
)
from app.application.commands.parse_page.handler import ParsePageHandler
from app.application.ports.comment_repository import (
    CommentRepositoryProtocol,
)
from app.application.ports.forum_parser import ForumParserProtocol
from app.application.queries.comments.get.handler import GetCommentQueryHandler
from app.application.queries.comments.list.handler import (
    GetCommentsQueryHandler,
)
from app.domain.clock import Clock


class HandlersProvider(Provider):
    """провайдер обработчиков команд и запросов прикладного слоя"""

    @provide(scope=Scope.REQUEST)
    def provide_parse_page_handler(
        self,
        parser: ForumParserProtocol,
        comments: CommentRepositoryProtocol,
        clock: Clock,
    ) -> ParsePageHandler:
        return ParsePageHandler(parser=parser, comments=comments, clock=clock)

    @provide(scope=Scope.REQUEST)
    def provide_add_comment_handler(
        self,
        comments: CommentRepositoryProtocol,
        clock: Clock,
    ) -> AddCommentHandler:
        return AddCommentHandler(comments=comments, clock=clock)

    @provide(scope=Scope.REQUEST)
    def provide_get_comment_query_handler(
        self, comments: CommentRepositoryProtocol
    ) -> GetCommentQueryHandler:
        return GetCommentQueryHandler(comments=comments)

    @provide(scope=Scope.REQUEST)
    def provide_get_comments_query_handler(
        self, comments: CommentRepositoryProtocol
    ) -> GetCommentsQueryHandler:
        return GetCommentsQueryHandler(comments=comments)

    @provide(scope=Scope.REQUEST)
    def provide_update_comment_handler(
        self,
        comments: CommentRepositoryProtocol,
        clock: Clock,
    ) -> UpdateCommentHandler:
        return UpdateCommentHandler(comments=comments, clock=clock)

    @provide(scope=Scope.REQUEST)
    def provide_delete_comment_handler(
        self, comments: CommentRepositoryProtocol
    ) -> DeleteCommentHandler:
        return DeleteCommentHandler(comments=comments)
